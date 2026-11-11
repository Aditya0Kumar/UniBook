from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    TYPE_BOOKING_CONFIRMED = 'booking_confirmed'
    TYPE_BOOKING_PENDING = 'booking_pending'
    TYPE_BOOKING_REJECTED = 'booking_rejected'
    TYPE_BOOKING_CANCELLED = 'booking_cancelled'
    TYPE_CHECK_IN = 'check_in'
    TYPE_MAINTENANCE = 'maintenance'
    TYPE_ANNOUNCEMENT = 'announcement'
    TYPE_REMINDER = 'reminder'

    NOTIFICATION_TYPES = [
        (TYPE_BOOKING_CONFIRMED, _('Booking Confirmed')),
        (TYPE_BOOKING_PENDING, _('Booking Pending Review')),
        (TYPE_BOOKING_REJECTED, _('Booking Rejected')),
        (TYPE_BOOKING_CANCELLED, _('Booking Cancelled')),
        (TYPE_CHECK_IN, _('Checked In')),
        (TYPE_MAINTENANCE, _('Facility Maintenance Notice')),
        (TYPE_ANNOUNCEMENT, _('Campus Announcement')),
        (TYPE_REMINDER, _('Booking Reminder')),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default=TYPE_BOOKING_CONFIRMED)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


class Announcement(models.Model):
    TARGET_ALL = 'all'
    TARGET_STUDENT = 'student'
    TARGET_FACULTY = 'faculty'
    TARGET_STAFF = 'staff'

    TARGET_CHOICES = [
        (TARGET_ALL, _('All Campus Community')),
        (TARGET_STUDENT, _('Students Only')),
        (TARGET_FACULTY, _('Faculty Only')),
        (TARGET_STAFF, _('Facility Managers / Staff Only')),
    ]

    CATEGORY_GENERAL = 'general'
    CATEGORY_MAINTENANCE = 'maintenance'
    CATEGORY_SPORTS = 'sports'
    CATEGORY_POLICY = 'policy'

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, _('General')),
        (CATEGORY_MAINTENANCE, _('Maintenance Alert')),
        (CATEGORY_SPORTS, _('Sports & Tournaments')),
        (CATEGORY_POLICY, _('Policy & Rules Update')),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    target_role = models.CharField(max_length=20, choices=TARGET_CHOICES, default=TARGET_ALL)
    is_active = models.BooleanField(default=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
