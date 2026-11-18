import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from apps.facilities.models import Facility, FacilityCategory
from apps.bookings.models import Booking
from apps.notifications.models import Notification, Announcement
from apps.maintenance.models import FacilityMaintenance
from apps.bookings.services import approve_booking, reject_booking, validate_and_checkin


@login_required
def student_dashboard(request):
    user = request.user
    today = timezone.localdate()

    upcoming_bookings = Booking.objects.filter(
        user=user,
        booking_date__gte=today,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
    ).select_related('facility', 'facility__category')[:5]

    total_bookings = Booking.objects.filter(user=user).count()
    completed_bookings = Booking.objects.filter(
        user=user,
        status__in=[Booking.STATUS_COMPLETED, Booking.STATUS_CHECKED_IN]
    ).count()
    pending_bookings = Booking.objects.filter(
        user=user,
        status=Booking.STATUS_PENDING
    ).count()

    popular_facilities = Facility.objects.filter(
        facility_status=Facility.STATUS_ACTIVE
    ).select_related('category')[:4]

    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(target_role=Announcement.TARGET_ALL) | Q(target_role=Announcement.TARGET_STUDENT)
    )[:4]

    context = {
        'upcoming_bookings': upcoming_bookings,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'popular_facilities': popular_facilities,
        'announcements': announcements,
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def faculty_dashboard(request):
    user = request.user
    today = timezone.localdate()

    # Academic facilities (Labs, Seminar Halls, Auditoriums, Conference Rooms)
    academic_categories = [
        'computer-laboratory', 'research-laboratory',
        'seminar-hall', 'auditorium', 'conference-room'
    ]
    academic_facilities = Facility.objects.filter(
        category__slug__in=academic_categories,
        facility_status=Facility.STATUS_ACTIVE
    ).select_related('category')

    my_academic_bookings = Booking.objects.filter(
        user=user
    ).select_related('facility', 'facility__category')[:10]

    pending_approvals_count = Booking.objects.filter(
        user=user,
        status=Booking.STATUS_PENDING
    ).count()

    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(target_role=Announcement.TARGET_ALL) | Q(target_role=Announcement.TARGET_FACULTY)
    )[:4]

    context = {
        'academic_facilities': academic_facilities,
        'my_academic_bookings': my_academic_bookings,
        'pending_approvals_count': pending_approvals_count,
        'announcements': announcements,
    }
    return render(request, 'faculty/dashboard.html', context)


@login_required
def staff_dashboard(request):
    user = request.user
    if not (user.is_facility_manager or user.is_superadmin):
        messages.error(request, "Access restricted to Facility Managers and Staff.")
        return redirect('student:dashboard')

    today = timezone.localdate()

    # If superadmin, see all; if facility manager, see assigned facilities
    if user.is_superadmin:
        managed_facilities = Facility.objects.all().select_related('category')
        pending_bookings = Booking.objects.filter(
            status=Booking.STATUS_PENDING
        ).select_related('facility', 'user')
        today_bookings = Booking.objects.filter(
            booking_date=today,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_CHECKED_IN]
        ).select_related('facility', 'user')
        active_maintenances = FacilityMaintenance.objects.filter(
            status__in=[FacilityMaintenance.STATUS_SCHEDULED, FacilityMaintenance.STATUS_IN_PROGRESS]
        ).select_related('facility')
    else:
        managed_facilities = Facility.objects.filter(assigned_manager=user).select_related('category')
        pending_bookings = Booking.objects.filter(
            facility__in=managed_facilities,
            status=Booking.STATUS_PENDING
        ).select_related('facility', 'user')
        today_bookings = Booking.objects.filter(
            facility__in=managed_facilities,
            booking_date=today,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_CHECKED_IN]
        ).select_related('facility', 'user')
        active_maintenances = FacilityMaintenance.objects.filter(
            facility__in=managed_facilities,
            status__in=[FacilityMaintenance.STATUS_SCHEDULED, FacilityMaintenance.STATUS_IN_PROGRESS]
        ).select_related('facility')

    # Quick checkin action from staff dashboard POST
    if request.method == 'POST' and 'token_or_reference' in request.POST:
        token_or_ref = request.POST.get('token_or_reference', '').strip()
        ip_address = request.META.get('REMOTE_ADDR')
        res = validate_and_checkin(token_or_ref, user, ip_address=ip_address)
        if res['success']:
            messages.success(request, res['message'])
        else:
            messages.error(request, res['message'])
        return redirect('staff:dashboard')

    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(target_role=Announcement.TARGET_ALL) | Q(target_role=Announcement.TARGET_STAFF)
    )[:4]

    context = {
        'announcements': announcements,
        'managed_facilities': managed_facilities,
        'pending_bookings': pending_bookings,
        'today_bookings': today_bookings,
        'active_maintenances': active_maintenances,
        'today': today,
    }
    return render(request, 'staff/dashboard.html', context)


@login_required
def staff_qr_scanner_view(request):
    user = request.user
    if not (user.is_facility_manager or user.is_superadmin):
        messages.error(request, "Access restricted to Facility Managers.")
        return redirect('student:dashboard')

    if request.method == 'POST':
        token_or_ref = request.POST.get('token_or_reference', '').strip()
        ip_address = request.META.get('REMOTE_ADDR')
        res = validate_and_checkin(token_or_ref, user, ip_address=ip_address)
        if res['success']:
            messages.success(request, res['message'])
        else:
            messages.error(request, res['message'])
        return redirect('staff:qr_scanner')

    recent_checkins = Booking.objects.filter(
        checked_in_by=user,
        status=Booking.STATUS_CHECKED_IN
    ).select_related('facility', 'user').order_by('-checked_in_at')[:10]

    context = {
        'recent_checkins': recent_checkins,
    }
    return render(request, 'staff/qr_scanner.html', context)


@login_required
def staff_approvals_view(request):
    user = request.user
    if not (user.is_facility_manager or user.is_superadmin):
        messages.error(request, "Access restricted to Facility Managers.")
        return redirect('student:dashboard')

    if user.is_superadmin:
        pending_bookings = Booking.objects.filter(
            status=Booking.STATUS_PENDING
        ).select_related('facility', 'user')
    else:
        pending_bookings = Booking.objects.filter(
            facility__assigned_manager=user,
            status=Booking.STATUS_PENDING
        ).select_related('facility', 'user')

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        if not (booking_id and str(booking_id).isdigit()):
            messages.error(request, "Invalid booking selected.")
            return redirect('staff:approvals')
        booking = get_object_or_404(Booking.objects.select_related('facility'), id=booking_id)
        if not user.can_manage_facility(booking.facility):
            messages.error(request, f"You are not the manager for {booking.facility.name}.")
            return redirect('staff:approvals')

        try:
            if action == 'approve':
                approve_booking(booking, user, comments=comments, ip_address=request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Booking {booking.booking_reference} has been approved.")
            elif action == 'reject':
                reject_booking(booking, user, reason=comments, ip_address=request.META.get('REMOTE_ADDR'))
                messages.warning(request, f"Booking {booking.booking_reference} has been rejected.")
        except Exception as e:
            messages.error(request, f"Action failed: {str(e)}")

        return redirect('staff:approvals')

    return render(request, 'staff/approvals.html', {'pending_bookings': pending_bookings})

