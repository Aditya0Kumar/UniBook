from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility
from apps.bookings.models import Booking


class EventAuditoriumDetail(models.Model):
    facility = models.OneToOneField(Facility, on_delete=models.CASCADE, related_name='auditorium_specs')
    stage_size = models.CharField(max_length=100, default='40x25 ft')
    audio_system = models.CharField(max_length=200, default='Dolby surround, 6 wireless microphones, mixer console')
    projector_specs = models.CharField(max_length=200, default='Dual 4K Laser Projectors + motorized screens')
    green_rooms_count = models.PositiveIntegerField(default=2)
    has_recording_equipment = models.BooleanField(default=True)

    def __str__(self):
        return f"Specs: {self.facility.name}"


class EventBookingDetail(models.Model):
    EVENT_TYPES = [
        ('academic_conference', _('Academic Conference')),
        ('seminar_symposium', _('Seminar / Symposium')),
        ('cultural_festival', _('Cultural Event / Fest')),
        ('guest_lecture', _('Distinguished Guest Lecture')),
        ('workshop_hackathon', _('Workshop / Hackathon')),
        ('club_meeting', _('Student Club / Society Event')),
        ('university_ceremony', _('Official University Ceremony')),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='event_details')
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES, default='seminar_symposium')
    event_title = models.CharField(max_length=200)
    organizer_department = models.CharField(max_length=150, blank=True)
    faculty_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_events'
    )
    expected_attendees = models.PositiveIntegerField(default=100)
    requires_av_support = models.BooleanField(default=True)
    requires_recording = models.BooleanField(default=False)
    catering_needed = models.BooleanField(default=False)
    special_guests = models.TextField(blank=True, help_text=_('VIP guests or keynote speaker details.'))

    def __str__(self):
        return f"{self.event_title} ({self.booking.booking_reference})"
