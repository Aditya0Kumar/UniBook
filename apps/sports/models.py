from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility
from apps.bookings.models import Booking


class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='trophy')
    is_team_sport = models.BooleanField(default=False)
    players_per_side = models.PositiveIntegerField(default=1)
    rules_summary = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SportsCourt(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='courts')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='courts')
    court_number = models.CharField(max_length=50) # e.g. Court 1, Pitch A, Lane 3
    surface_type = models.CharField(max_length=50, blank=True) # Synthetic, Hardwood, Grass, Clay
    is_indoor = models.BooleanField(default=True)

    class Meta:
        unique_together = ('facility', 'court_number')

    def __str__(self):
        return f"{self.facility.name} - {self.court_number} ({self.sport.name})"


class SportsEquipment(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='equipment')
    name = models.CharField(max_length=100) # Racket, Shuttlecock tube, Football, Basketball
    total_quantity = models.PositiveIntegerField(default=10)
    available_quantity = models.PositiveIntegerField(default=10)
    rental_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.sport.name}) - {self.available_quantity}/{self.total_quantity} avail"


class SportsReservation(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='sports_details')
    court = models.ForeignKey(SportsCourt, on_delete=models.SET_NULL, null=True, blank=True)
    sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True)
    is_team_booking = models.BooleanField(default=False)
    team_name = models.CharField(max_length=100, blank=True)
    equipment_needed = models.CharField(max_length=200, blank=True)
    coach_requested = models.BooleanField(default=False)

    def __str__(self):
        return f"Sports Booking {self.booking.booking_reference} ({self.sport.name if self.sport else 'Court'})"
