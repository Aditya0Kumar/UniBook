import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_NO_SHOW = 'no_show'
    STATUS_PAYMENT_PENDING = 'payment_pending'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending Approval')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_REJECTED, _('Rejected')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CHECKED_IN, _('Checked In')),
        (STATUS_NO_SHOW, _('No Show')),
        (STATUS_PAYMENT_PENDING, _('Payment Pending')),
    ]

    PAYMENT_FREE = 'free'
    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_FAILED = 'failed'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_FREE, _('Free Facility')),
        (PAYMENT_PENDING, _('Pending')),
        (PAYMENT_PAID, _('Paid')),
        (PAYMENT_REFUNDED, _('Refunded')),
        (PAYMENT_FAILED, _('Failed')),
    ]

    booking_reference = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
        help_text=_('Unique public human-readable reference, e.g. UB-20261111-A89BC')
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text=_('Cryptographic token for QR pass validation.')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    booking_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    participant_count = models.PositiveIntegerField(default=1)
    purpose = models.TextField(help_text=_('Purpose of booking or event title.'))
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CONFIRMED,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_FREE,
        db_index=True
    )
    qr_code = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    
    # Approvals & Check-in
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_bookings'
    )
    rejection_reason = models.TextField(blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_checkins'
    )

    # Faculty special request / recurring flag
    is_recurring = models.BooleanField(default=False)
    recurring_rule = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-start_time']
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        indexes = [
            models.Index(fields=['facility', 'booking_date', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            date_str = self.booking_date.strftime('%Y%m%d') if self.booking_date else timezone.now().strftime('%Y%m%d')
            rand_suffix = secrets.token_hex(3).upper()
            self.booking_reference = f"UB-{date_str}-{rand_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.facility.name} ({self.booking_date})"

    @property
    def is_past(self):
        now = timezone.now()
        booking_datetime = timezone.make_aware(
            timezone.datetime.combine(self.booking_date, self.end_time)
        )
        return booking_datetime < now

    @property
    def can_be_cancelled(self):
        if self.status not in [self.STATUS_PENDING, self.STATUS_CONFIRMED]:
            return False
        # Check cancellation deadline
        now = timezone.now()
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(self.booking_date, self.start_time)
        )
        deadline = start_datetime - timezone.timedelta(hours=self.facility.cancellation_deadline)
        return now <= deadline


class BookingParticipant(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='participants')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    university_id = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=50, blank=True, help_text=_('e.g. Co-presenter, Team member, Attendee'))

    def __str__(self):
        return f"{self.name} ({self.booking.booking_reference})"


class BookingCancellation(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='cancellation_record')
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    reason = models.TextField()
    cancelled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cancellation of {self.booking.booking_reference}"


class BookingApproval(models.Model):
    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_CHOICES = [
        (ACTION_APPROVED, _('Approved')),
        (ACTION_REJECTED, _('Rejected')),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='approval_history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action.capitalize()} by {self.action_by} for {self.booking.booking_reference}"
