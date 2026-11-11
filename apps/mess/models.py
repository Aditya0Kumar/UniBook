from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility
from apps.bookings.models import Booking


class Meal(models.Model):
    MEAL_BREAKFAST = 'breakfast'
    MEAL_LUNCH = 'lunch'
    MEAL_SNACKS = 'snacks'
    MEAL_DINNER = 'dinner'

    MEAL_TYPES = [
        (MEAL_BREAKFAST, _('Breakfast (07:30 - 09:30)')),
        (MEAL_LUNCH, _('Lunch (12:00 - 14:30)')),
        (MEAL_SNACKS, _('Evening Snacks (17:00 - 18:30)')),
        (MEAL_DINNER, _('Dinner (19:30 - 21:45)')),
    ]

    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, unique=True)
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    default_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class MealMenu(models.Model):
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='meal_menus')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='menus')
    dishes = models.TextField(help_text=_('Menu items separated by commas or lines'))
    special_dietary_options = models.CharField(max_length=200, blank=True, help_text=_('e.g. Jain counter, Vegan option, Fruit bowl'))
    calories_approx = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('facility', 'day_of_week', 'meal')
        ordering = ['day_of_week', 'meal__start_time']

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK).get(self.day_of_week, '')
        return f"{self.facility.name} - {day_name} {self.meal.name}"


class DietaryPreference(models.Model):
    PREF_VEG = 'veg'
    PREF_NON_VEG = 'non_veg'
    PREF_VEGAN = 'vegan'
    PREF_JAIN = 'jain'
    PREF_HALAL = 'halal'

    PREF_CHOICES = [
        (PREF_VEG, _('Vegetarian')),
        (PREF_NON_VEG, _('Non-Vegetarian')),
        (PREF_VEGAN, _('Vegan')),
        (PREF_JAIN, _('Jain')),
        (PREF_HALAL, _('Halal')),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dietary_preference')
    preference = models.CharField(max_length=20, choices=PREF_CHOICES, default=PREF_VEG)
    allergies = models.CharField(max_length=250, blank=True, help_text=_('e.g. Peanut, Gluten, Lactose'))

    def __str__(self):
        return f"{self.user.username}: {self.get_preference_display()}"


class MealReservation(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='meal_details')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    dietary_choice = models.CharField(max_length=30, blank=True)
    special_request = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.meal.name}"
