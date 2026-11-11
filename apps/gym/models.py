from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility
from apps.bookings.models import Booking


class Trainer(models.Model):
    name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=150, help_text=_('e.g. Strength & Conditioning, HIIT, Pilates, Yoga'))
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='gym/trainers/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.specialization}"


class GymSession(models.Model):
    SESSION_MORNING = 'morning'
    SESSION_AFTERNOON = 'afternoon'
    SESSION_EVENING = 'evening'
    SESSION_CHOICES = [
        (SESSION_MORNING, _('Morning Session (06:00 - 10:00)')),
        (SESSION_AFTERNOON, _('Afternoon Session (12:00 - 16:00)')),
        (SESSION_EVENING, _('Evening Session (17:00 - 22:00)')),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='gym_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_CHOICES)
    title = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=40)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class GymMembership(models.Model):
    PLAN_MONTHLY = 'monthly'
    PLAN_SEMESTER = 'semester'
    PLAN_ANNUAL = 'annual'
    PLAN_CHOICES = [
        (PLAN_MONTHLY, _('Monthly Plan')),
        (PLAN_SEMESTER, _('Semester Pass')),
        (PLAN_ANNUAL, _('Annual Pass')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gym_memberships')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_SEMESTER)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_plan_display()}"


class GymReservation(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='gym_details')
    session = models.ForeignKey(GymSession, on_delete=models.SET_NULL, null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True)
    workout_goal = models.CharField(max_length=150, blank=True, help_text=_('Cardio, Weights, Core, etc.'))

    def __str__(self):
        return f"Gym reservation for {self.booking.booking_reference}"
