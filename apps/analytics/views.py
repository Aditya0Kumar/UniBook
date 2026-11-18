import csv
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate, ExtractHour
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.models import CustomUser, Department
from apps.facilities.models import Facility, FacilityCategory
from apps.bookings.models import Booking
from apps.maintenance.models import FacilityMaintenance
from apps.reviews.models import Complaint, Review
from apps.notifications.models import Announcement
from apps.payments.models import Payment
from apps.accounts.permissions import IsSuperAdmin
from .models import AuditLog


def _get_posted_object(model, raw_id):
    """get_object_or_404 for an id taken from POST data; non-numeric ids give a 404 instead of a 500."""
    if not (raw_id and str(raw_id).isdigit()):
        raise Http404("Invalid id")
    return get_object_or_404(model, id=raw_id)


@login_required
def admin_dashboard_view(request):
    if not request.user.is_superadmin:
        messages.error(request, "Access restricted to Super Administrators.")
        return redirect('public:home')

    today = timezone.localdate()
    total_users = CustomUser.objects.count()
    total_facilities = Facility.objects.count()
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(
        booking_date__gte=today,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
    ).count()
    pending_approvals = Booking.objects.filter(status=Booking.STATUS_PENDING).count()
    total_revenue = Payment.objects.filter(
        status=Payment.STATUS_COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0
    active_maintenances = FacilityMaintenance.objects.filter(
        status__in=[FacilityMaintenance.STATUS_SCHEDULED, FacilityMaintenance.STATUS_IN_PROGRESS]
    ).count()

    # Recent Audit Logs
    recent_logs = AuditLog.objects.select_related('user')[:8]

    # Recent Pending Complaints
    pending_complaints = Complaint.objects.filter(
        status=Complaint.STATUS_PENDING
    ).select_related('facility', 'user')[:5]

    context = {
        'total_users': total_users,
        'total_facilities': total_facilities,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'pending_approvals': pending_approvals,
        'total_revenue': total_revenue,
        'active_maintenances': active_maintenances,
        'recent_logs': recent_logs,
        'pending_complaints': pending_complaints,
    }
    return render(request, 'admin_panel/dashboard.html', context)


class AdminAnalyticsAPIView(APIView):
    """
    Returns aggregated JSON datasets for Chart.js rendering on the Admin Dashboard.
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        today = timezone.localdate()
        seven_days_ago = today - datetime.timedelta(days=6)

        # 1. Booking Trends by Date (Last 7 Days)
        trend_query = Booking.objects.filter(
            booking_date__gte=seven_days_ago,
            booking_date__lte=today
        ).values('booking_date').annotate(count=Count('id')).order_by('booking_date')

        date_dict = {
            (seven_days_ago + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): 0
            for i in range(7)
        }
        for item in trend_query:
            date_dict[item['booking_date'].strftime('%Y-%m-%d')] = item['count']

        booking_trends = {
            'labels': [datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%a, %b %d') for d in date_dict.keys()],
            'data': list(date_dict.values())
        }

        # 2. Facility Category Distribution
        cat_query = Facility.objects.values(
            'category__name'
        ).annotate(count=Count('bookings')).order_by('-count')[:6]

        category_distribution = {
            'labels': [item['category__name'] for item in cat_query],
            'data': [item['count'] for item in cat_query]
        }

        # 3. Peak Booking Hours
        hour_query = Booking.objects.annotate(
            hour=ExtractHour('start_time')
        ).values('hour').annotate(count=Count('id')).order_by('hour')

        hour_map = {h: 0 for h in range(8, 22)}
        for item in hour_query:
            h = item['hour']
            if h in hour_map:
                hour_map[h] = item['count']

        peak_hours = {
            'labels': [f"{h:02d}:00" for h in hour_map.keys()],
            'data': list(hour_map.values())
        }

        # 4. Status Breakdown
        status_query = Booking.objects.values('status').annotate(count=Count('id'))
        status_data = {
            'labels': [item['status'].replace('_', ' ').title() for item in status_query],
            'data': [item['count'] for item in status_query]
        }

        return Response({
            'booking_trends': booking_trends,
            'category_distribution': category_distribution,
            'peak_hours': peak_hours,
            'status_breakdown': status_data,
        })


@login_required
def admin_facilities_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    facilities = Facility.objects.select_related('category', 'assigned_manager').all()
    categories = FacilityCategory.objects.all()

    if request.method == 'POST' and 'toggle_status' in request.POST:
        fac_id = request.POST.get('facility_id')
        facility = _get_posted_object(Facility, fac_id)
        if facility.facility_status == Facility.STATUS_ACTIVE:
            facility.facility_status = Facility.STATUS_MAINTENANCE
        else:
            facility.facility_status = Facility.STATUS_ACTIVE
        facility.save()
        messages.success(request, f"Updated status of '{facility.name}' to {facility.get_facility_status_display()}.")
        return redirect('admin_panel:facilities')

    return render(request, 'admin_panel/facilities.html', {
        'facilities': facilities,
        'categories': categories,
    })


@login_required
def admin_users_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    role_filter = request.GET.get('role', '')
    users = CustomUser.objects.select_related('department').all()
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'admin_panel/users.html', {
        'users': users,
        'role_filter': role_filter,
    })


@login_required
def admin_bookings_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    bookings = Booking.objects.select_related('facility', 'user', 'facility__category').all()[:50]
    return render(request, 'admin_panel/bookings.html', {'bookings': bookings})


@login_required
def admin_export_bookings_csv(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="unibook_reservations_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reference', 'Facility', 'Category', 'User Name', 'User Email',
        'Date', 'Start Time', 'End Time', 'Participants', 'Status', 'Payment Status', 'Created At'
    ])

    bookings = Booking.objects.select_related('facility', 'user', 'facility__category').all()
    for b in bookings:
        writer.writerow([
            b.booking_reference,
            b.facility.name,
            b.facility.category.name,
            b.user.get_full_name() or b.user.username,
            b.user.email,
            b.booking_date,
            b.start_time.strftime('%H:%M'),
            b.end_time.strftime('%H:%M'),
            b.participant_count,
            b.get_status_display(),
            b.get_payment_status_display(),
            b.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


@login_required
def admin_export_facilities_csv(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="unibook_facilities_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Facility ID', 'Name', 'Category', 'Campus', 'Building', 'Floor',
        'Capacity', 'Is Exclusive', 'Status', 'Price', 'Approval Required'
    ])

    facilities = Facility.objects.select_related('category').all()
    for f in facilities:
        writer.writerow([
            f.id, f.name, f.category.name, f.campus, f.building, f.floor,
            f.capacity, f.is_exclusive, f.facility_status, f.booking_price, f.approval_requirement
        ])

    return response


@login_required
def admin_maintenance_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    facilities = Facility.objects.all()
    records = FacilityMaintenance.objects.select_related('facility', 'created_by').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            fac_id = request.POST.get('facility_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            start_str = request.POST.get('start_time')
            end_str = request.POST.get('end_time')

            try:
                if not (title or '').strip():
                    raise ValueError("a title is required")
                start_dt = timezone.datetime.fromisoformat(start_str)
                end_dt = timezone.datetime.fromisoformat(end_str)
                if end_dt <= start_dt:
                    raise ValueError("end time must be after start time")
                facility = _get_posted_object(Facility, fac_id)
                FacilityMaintenance.objects.create(
                    facility=facility,
                    title=title.strip(),
                    description=description or '',
                    start_time=timezone.make_aware(start_dt) if timezone.is_naive(start_dt) else start_dt,
                    end_time=timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt,
                    status=FacilityMaintenance.STATUS_SCHEDULED,
                    created_by=request.user
                )
                messages.success(request, f"Scheduled maintenance for '{facility.name}'.")
            except Exception as e:
                messages.error(request, f"Failed to schedule maintenance: {str(e)}")

        elif action == 'complete':
            record_id = request.POST.get('record_id')
            m_record = _get_posted_object(FacilityMaintenance, record_id)
            m_record.status = FacilityMaintenance.STATUS_COMPLETED
            m_record.save()
            messages.success(request, f"Marked maintenance '{m_record.title}' as completed.")

        return redirect('admin_panel:maintenance')

    return render(request, 'admin_panel/maintenance.html', {
        'records': records,
        'facilities': facilities,
    })


@login_required
def admin_complaints_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    complaints = Complaint.objects.select_related('facility', 'user', 'resolved_by').all()

    if request.method == 'POST':
        c_id = request.POST.get('complaint_id')
        new_status = request.POST.get('status')
        remarks = request.POST.get('admin_remarks', '')

        complaint = _get_posted_object(Complaint, c_id)
        valid_statuses = {choice[0] for choice in Complaint._meta.get_field('status').choices}
        if new_status not in valid_statuses:
            messages.error(request, "Please choose a valid complaint status.")
            return redirect('admin_panel:complaints')
        complaint.status = new_status
        complaint.admin_remarks = remarks
        if new_status == Complaint.STATUS_RESOLVED:
            complaint.resolved_by = request.user
        complaint.save()

        messages.success(request, f"Updated complaint #{complaint.id} to '{complaint.get_status_display()}'.")
        return redirect('admin_panel:complaints')

    return render(request, 'admin_panel/complaints.html', {'complaints': complaints})


@login_required
def admin_announcements_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    announcements = Announcement.objects.select_related('author').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            title = (request.POST.get('title') or '').strip()
            content = (request.POST.get('content') or '').strip()
            category = request.POST.get('category', Announcement.CATEGORY_GENERAL)
            target = request.POST.get('target_role', Announcement.TARGET_ALL)

            if not title or not content:
                messages.error(request, "An announcement needs both a title and content.")
                return redirect('admin_panel:announcements')
            valid_categories = {c[0] for c in Announcement._meta.get_field('category').choices}
            valid_targets = {t[0] for t in Announcement._meta.get_field('target_role').choices}
            if category not in valid_categories:
                category = Announcement.CATEGORY_GENERAL
            if target not in valid_targets:
                target = Announcement.TARGET_ALL

            Announcement.objects.create(
                title=title,
                content=content,
                category=category,
                target_role=target,
                author=request.user,
                is_active=True
            )
            messages.success(request, "New announcement published to campus community.")
        elif action == 'toggle':
            ann_id = request.POST.get('announcement_id')
            ann = _get_posted_object(Announcement, ann_id)
            ann.is_active = not ann.is_active
            ann.save()
            messages.success(request, f"Updated announcement '{ann.title}' status.")

        return redirect('admin_panel:announcements')

    return render(request, 'admin_panel/announcements.html', {'announcements': announcements})


@login_required
def admin_payments_view(request):
    if not request.user.is_superadmin:
        return redirect('public:home')

    payments = Payment.objects.select_related('booking', 'user', 'booking__facility').all()
    total_rev = payments.filter(status=Payment.STATUS_COMPLETED).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'admin_panel/payments.html', {
        'payments': payments,
        'total_revenue': total_rev,
    })
