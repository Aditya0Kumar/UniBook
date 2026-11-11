import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, Q

from apps.facilities.models import Facility, FacilityOperatingHour, Holiday
from apps.maintenance.models import FacilityMaintenance
from apps.notifications.models import Notification
from apps.analytics.models import AuditLog
from .models import Booking, BookingCancellation, BookingApproval
from .qr import generate_qr_code_image


def get_facility_operating_hours_for_date(facility: Facility, target_date: datetime.date):
    """
    Returns (opening_time, closing_time, is_closed) for the facility on target_date.
    Checks day-of-week overrides, available_days, and holidays.
    """
    # 1. Check if date is university holiday
    if Holiday.objects.filter(date=target_date, is_university_wide=True).exists():
        return None, None, True

    # 2. Check facility status
    if facility.facility_status != Facility.STATUS_ACTIVE:
        return None, None, True

    weekday = target_date.weekday() # 0 = Monday, 6 = Sunday

    # 3. Check facility available_days list if specified
    if facility.available_days and len(facility.available_days) > 0:
        if weekday not in facility.available_days and str(weekday) not in facility.available_days:
            return None, None, True

    # 4. Check FacilityOperatingHour override
    op_hour = FacilityOperatingHour.objects.filter(facility=facility, day_of_week=weekday).first()
    if op_hour:
        if op_hour.is_closed:
            return None, None, True
        return op_hour.opening_time, op_hour.closing_time, False

    # Default to facility main opening/closing times
    return facility.opening_time, facility.closing_time, False


def calculate_facility_slots(facility: Facility, target_date: datetime.date):
    """
    Calculates time slots for a given facility on target_date, returning availability,
    capacity, and booking status.
    """
    opening_time, closing_time, is_closed = get_facility_operating_hours_for_date(facility, target_date)
    if is_closed or not opening_time or not closing_time:
        return []

    slot_duration_mins = facility.slot_duration or 60
    slot_delta = datetime.timedelta(minutes=slot_duration_mins)

    # Fetch active maintenance windows for this facility that overlap this date
    start_of_day = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time.min))
    end_of_day = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time.max))

    maintenances = FacilityMaintenance.objects.filter(
        facility=facility,
        status__in=[FacilityMaintenance.STATUS_SCHEDULED, FacilityMaintenance.STATUS_IN_PROGRESS],
        start_time__lte=end_of_day,
        end_time__gte=start_of_day
    )

    # Fetch active bookings for this facility on target_date
    active_bookings = Booking.objects.filter(
        facility=facility,
        booking_date=target_date,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING, Booking.STATUS_CHECKED_IN]
    )

    slots = []
    current_time = opening_time

    # Generate slots from opening_time up to closing_time
    while True:
        current_dt = datetime.datetime.combine(target_date, current_time)
        slot_end_dt = current_dt + slot_delta
        slot_end_time = slot_end_dt.time()

        if slot_end_time > closing_time and slot_end_dt.date() == target_date:
            break

        # Check maintenance overlap
        slot_start_aware = timezone.make_aware(current_dt)
        slot_end_aware = timezone.make_aware(slot_end_dt)
        in_maintenance = any(
            m.start_time < slot_end_aware and m.end_time > slot_start_aware
            for m in maintenances
        )

        # Check existing bookings overlapping this slot
        overlapping_bookings = active_bookings.filter(
            start_time__lt=slot_end_time,
            end_time__gt=current_time
        )

        is_available = True
        remaining_capacity = facility.capacity

        if in_maintenance:
            is_available = False
            remaining_capacity = 0
            reason = "Under Maintenance"
        else:
            if facility.is_exclusive:
                if overlapping_bookings.exists():
                    is_available = False
                    remaining_capacity = 0
                    reason = "Reserved"
                else:
                    reason = "Available"
            else:
                total_participants = overlapping_bookings.aggregate(
                    total=Sum('participant_count')
                )['total'] or 0
                remaining_capacity = max(0, facility.capacity - total_participants)
                if remaining_capacity <= 0:
                    is_available = False
                    reason = "Fully Booked"
                else:
                    reason = f"{remaining_capacity} spots left"

        # Check if slot is already in the past
        now = timezone.now()
        if slot_start_aware < now:
            is_available = False
            reason = "Past"

        slots.append({
            'start_time': current_time.strftime('%H:%M'),
            'end_time': slot_end_time.strftime('%H:%M'),
            'is_available': is_available,
            'remaining_capacity': remaining_capacity,
            'status_label': reason,
        })

        if slot_end_time >= closing_time or slot_end_dt.date() > target_date:
            break
        current_time = slot_end_time

    return slots


@transaction.atomic
def create_booking(
    user,
    facility_id: int,
    booking_date: datetime.date,
    start_time: datetime.time,
    end_time: datetime.time,
    participant_count: int = 1,
    purpose: str = '',
    is_recurring: bool = False,
    recurring_rule: str = '',
    ip_address: str = None
) -> Booking:
    """
    Creates a new reservation with database-level concurrency protection using
    select_for_update() to lock overlapping records and prevent double-booking.
    """
    # 1. Lock the facility record
    facility = Facility.objects.select_for_update().get(id=facility_id)

    # 2. Basic status checks
    if facility.facility_status != Facility.STATUS_ACTIVE:
        raise ValidationError(f"Facility '{facility.name}' is currently {facility.get_facility_status_display()} and cannot be booked.")

    # 3. Advance booking limit
    today = timezone.localdate()
    if booking_date < today:
        raise ValidationError("Cannot make reservations for past dates.")

    max_date = today + datetime.timedelta(days=facility.max_advance_booking_days)
    if booking_date > max_date:
        raise ValidationError(f"Bookings are only permitted up to {facility.max_advance_booking_days} days in advance (until {max_date}).")

    # 4. Role restrictions for academic laboratories & auditoriums
    cat_slug = facility.category.slug
    if cat_slug in ['computer-laboratory', 'research-laboratory'] and user.is_student:
        # Students can book labs only if supervised or approval required
        facility.approval_requirement = True

    # 5. Operating hours validation
    opening_time, closing_time, is_closed = get_facility_operating_hours_for_date(facility, booking_date)
    if is_closed:
        raise ValidationError("The facility is closed on the selected date.")
    if start_time < opening_time or end_time > closing_time or start_time >= end_time:
        raise ValidationError(f"Booking times must be within operating hours ({opening_time.strftime('%H:%M')} - {closing_time.strftime('%H:%M')}).")

    # 6. Duration checks
    booking_start_dt = datetime.datetime.combine(booking_date, start_time)
    booking_end_dt = datetime.datetime.combine(booking_date, end_time)
    duration_mins = (booking_end_dt - booking_start_dt).total_seconds() / 60
    if duration_mins < facility.min_booking_duration:
        raise ValidationError(f"Minimum reservation duration is {facility.min_booking_duration} minutes.")
    if duration_mins > facility.max_booking_duration:
        raise ValidationError(f"Maximum reservation duration is {facility.max_booking_duration} minutes.")

    # 7. Check for past slot
    slot_start_aware = timezone.make_aware(booking_start_dt)
    if slot_start_aware < timezone.now():
        raise ValidationError("Cannot book a time slot that has already passed.")

    # 8. Check maintenance window
    slot_end_aware = timezone.make_aware(booking_end_dt)
    maintenance_conflict = FacilityMaintenance.objects.filter(
        facility=facility,
        status__in=[FacilityMaintenance.STATUS_SCHEDULED, FacilityMaintenance.STATUS_IN_PROGRESS],
        start_time__lt=slot_end_aware,
        end_time__gt=slot_start_aware
    ).exists()
    if maintenance_conflict:
        raise ValidationError("The facility is blocked for scheduled maintenance during this time.")

    # 9. Concurrency Protection & Overlap Prevention
    # Lock existing overlapping active bookings for this facility
    overlapping_query = Booking.objects.select_for_update().filter(
        facility=facility,
        booking_date=booking_date,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING, Booking.STATUS_CHECKED_IN],
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if facility.is_exclusive:
        if overlapping_query.exists():
            conflict = overlapping_query.first()
            raise ValidationError(
                f"Conflict detected: This facility is already reserved from {conflict.start_time.strftime('%H:%M')} to {conflict.end_time.strftime('%H:%M')}."
            )
    else:
        # Shared facility (e.g. Gym, Mess)
        current_reserved_count = overlapping_query.aggregate(total=Sum('participant_count'))['total'] or 0
        if current_reserved_count + participant_count > facility.capacity:
            available_spots = max(0, facility.capacity - current_reserved_count)
            raise ValidationError(
                f"Capacity exceeded: Only {available_spots} spot(s) remaining for this slot."
            )

    # 10. Status and Payment Status Determination
    if facility.approval_requirement:
        initial_status = Booking.STATUS_PENDING
    else:
        initial_status = Booking.STATUS_CONFIRMED

    if facility.booking_price > 0:
        initial_payment = Booking.PAYMENT_PENDING
    else:
        initial_payment = Booking.PAYMENT_FREE

    # 11. Create Booking instance
    booking = Booking(
        user=user,
        facility=facility,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        participant_count=participant_count,
        purpose=purpose,
        status=initial_status,
        payment_status=initial_payment,
        is_recurring=is_recurring,
        recurring_rule=recurring_rule
    )
    booking.save()

    # 12. Generate and attach QR pass image
    qr_file = generate_qr_code_image(str(booking.token), booking.booking_reference)
    booking.qr_code.save(qr_file.name, qr_file, save=True)

    # 13. Create In-App Notification
    if initial_status == Booking.STATUS_CONFIRMED:
        notif_msg = f"Your reservation for {facility.name} on {booking_date} ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}) is confirmed!"
        notif_type = Notification.TYPE_BOOKING_CONFIRMED
    else:
        notif_msg = f"Your reservation request for {facility.name} on {booking_date} has been submitted for manager approval."
        notif_type = Notification.TYPE_BOOKING_PENDING

    Notification.objects.create(
        recipient=user,
        title=f"Booking {booking.booking_reference}",
        message=notif_msg,
        notification_type=notif_type,
        link=f"/bookings/{booking.id}/"
    )

    # Also notify assigned manager if pending approval
    if initial_status == Booking.STATUS_PENDING and facility.assigned_manager:
        Notification.objects.create(
            recipient=facility.assigned_manager,
            title="New Approval Request",
            message=f"{user.get_full_name() or user.username} requested booking for {facility.name} on {booking_date}.",
            notification_type=Notification.TYPE_BOOKING_PENDING,
            link=f"/staff/approvals/"
        )

    # 14. Audit Log
    AuditLog.objects.create(
        user=user,
        action=f"Booking Created ({booking.booking_reference})",
        resource_type="Booking",
        resource_id=str(booking.id),
        ip_address=ip_address,
        details=f"Facility: {facility.name}, Date: {booking_date}, Time: {start_time}-{end_time}, Status: {initial_status}"
    )

    return booking


@transaction.atomic
def cancel_booking(booking: Booking, user, reason: str = '', ip_address: str = None) -> Booking:
    """
    Cancels a booking after verifying cancellation rules and permissions.
    """
    # Verify permission: only the booking owner or staff/admin can cancel
    if booking.user != user and not (user.is_staff or user.is_facility_manager or user.is_superadmin):
        raise ValidationError("You do not have permission to cancel this booking.")

    if not booking.can_be_cancelled:
        raise ValidationError("This booking cannot be cancelled because the cancellation deadline has passed or it is already closed.")

    booking.status = Booking.STATUS_CANCELLED
    if booking.payment_status == Booking.PAYMENT_PAID:
        booking.payment_status = Booking.PAYMENT_REFUNDED
    booking.save()

    BookingCancellation.objects.create(
        booking=booking,
        cancelled_by=user,
        reason=reason or "User cancelled reservation"
    )

    Notification.objects.create(
        recipient=booking.user,
        title="Booking Cancelled",
        message=f"Your reservation {booking.booking_reference} for {booking.facility.name} has been cancelled.",
        notification_type=Notification.TYPE_BOOKING_CANCELLED,
        link=f"/bookings/{booking.id}/"
    )

    AuditLog.objects.create(
        user=user,
        action=f"Booking Cancelled ({booking.booking_reference})",
        resource_type="Booking",
        resource_id=str(booking.id),
        ip_address=ip_address,
        details=f"Cancelled by {user.username}. Reason: {reason}"
    )

    return booking


@transaction.atomic
def approve_booking(booking: Booking, manager, comments: str = '', ip_address: str = None) -> Booking:
    """
    Approves a pending booking.
    """
    if booking.status != Booking.STATUS_PENDING:
        raise ValidationError("Only pending bookings can be approved.")

    booking.status = Booking.STATUS_CONFIRMED
    booking.approved_by = manager
    booking.save()

    BookingApproval.objects.create(
        booking=booking,
        action=BookingApproval.ACTION_APPROVED,
        action_by=manager,
        comments=comments
    )

    Notification.objects.create(
        recipient=booking.user,
        title="Booking Approved!",
        message=f"Good news! Your booking {booking.booking_reference} for {booking.facility.name} has been approved.",
        notification_type=Notification.TYPE_BOOKING_CONFIRMED,
        link=f"/bookings/{booking.id}/"
    )

    AuditLog.objects.create(
        user=manager,
        action=f"Booking Approved ({booking.booking_reference})",
        resource_type="Booking",
        resource_id=str(booking.id),
        ip_address=ip_address,
        details=f"Approved by {manager.username}. Comments: {comments}"
    )

    return booking


@transaction.atomic
def reject_booking(booking: Booking, manager, reason: str = '', ip_address: str = None) -> Booking:
    """
    Rejects a pending booking.
    """
    if booking.status != Booking.STATUS_PENDING:
        raise ValidationError("Only pending bookings can be rejected.")

    booking.status = Booking.STATUS_REJECTED
    booking.approved_by = manager
    booking.rejection_reason = reason or "Booking rejected by facility management."
    booking.save()

    BookingApproval.objects.create(
        booking=booking,
        action=BookingApproval.ACTION_REJECTED,
        action_by=manager,
        comments=reason
    )

    Notification.objects.create(
        recipient=booking.user,
        title="Booking Request Declined",
        message=f"Your booking request {booking.booking_reference} for {booking.facility.name} was declined. Reason: {reason}",
        notification_type=Notification.TYPE_BOOKING_REJECTED,
        link=f"/bookings/{booking.id}/"
    )

    AuditLog.objects.create(
        user=manager,
        action=f"Booking Rejected ({booking.booking_reference})",
        resource_type="Booking",
        resource_id=str(booking.id),
        ip_address=ip_address,
        details=f"Rejected by {manager.username}. Reason: {reason}"
    )

    return booking


@transaction.atomic
def validate_and_checkin(token_or_reference: str, staff_user, ip_address: str = None) -> dict:
    """
    Validates QR scan pass and marks reservation as Checked In.
    Guarantees no duplicate / replay check-in.
    """
    token_str = token_or_reference.strip()
    if token_str.startswith("UNIBOOK:"):
        parts = token_str.split(":")
        if len(parts) >= 2:
            token_str = parts[1]

    # Look up by token or booking_reference
    booking = Booking.objects.select_for_update().filter(
        Q(token__iexact=token_str) | Q(booking_reference__iexact=token_str)
    ).first()

    if not booking:
        return {
            'success': False,
            'message': 'Invalid QR pass: No corresponding reservation found.',
            'booking': None
        }

    # If facility manager is assigned, verify facility access
    if staff_user.role == 'facility_manager' and not staff_user.is_superuser:
        if booking.facility.assigned_manager_id and booking.facility.assigned_manager_id != staff_user.id:
            return {
                'success': False,
                'message': f"Access Denied: You are not the manager for {booking.facility.name}.",
                'booking': booking
            }

    # Check status
    if booking.status == Booking.STATUS_CHECKED_IN:
        return {
            'success': False,
            'message': f"Replay prevented: Booking {booking.booking_reference} was ALREADY checked in at {booking.checked_in_at.strftime('%Y-%m-%d %H:%M')}.",
            'booking': booking
        }

    if booking.status == Booking.STATUS_CANCELLED:
        return {
            'success': False,
            'message': f"Pass Rejected: Booking {booking.booking_reference} was CANCELLED.",
            'booking': booking
        }

    if booking.status == Booking.STATUS_REJECTED:
        return {
            'success': False,
            'message': f"Pass Rejected: Booking {booking.booking_reference} was REJECTED.",
            'booking': booking
        }

    if booking.status == Booking.STATUS_PENDING:
        return {
            'success': False,
            'message': f"Pass Pending: Booking {booking.booking_reference} has NOT yet been approved.",
            'booking': booking
        }

    # Check date
    today = timezone.localdate()
    if booking.booking_date != today:
        return {
            'success': False,
            'message': f"Date mismatch: This pass is valid for {booking.booking_date}, not today ({today}).",
            'booking': booking
        }

    # Valid check-in!
    now = timezone.now()
    booking.status = Booking.STATUS_CHECKED_IN
    booking.checked_in_at = now
    booking.checked_in_by = staff_user
    booking.save()

    Notification.objects.create(
        recipient=booking.user,
        title="Checked In Successfully",
        message=f"Welcome to {booking.facility.name}! Your entry pass was verified at {now.strftime('%H:%M')}.",
        notification_type=Notification.TYPE_CHECK_IN,
        link=f"/bookings/{booking.id}/"
    )

    AuditLog.objects.create(
        user=staff_user,
        action=f"QR Pass Validated & Checked In ({booking.booking_reference})",
        resource_type="Booking",
        resource_id=str(booking.id),
        ip_address=ip_address,
        details=f"User: {booking.user.username}, Facility: {booking.facility.name}, Verified by {staff_user.username}"
    )

    return {
        'success': True,
        'message': f"Pass Verified! Checked in {booking.user.get_full_name() or booking.user.username} for {booking.facility.name}.",
        'booking': booking
    }
