from django.contrib import admin
from .models import Meal, MealMenu, DietaryPreference, MealReservation


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'start_time', 'end_time', 'default_price')


@admin.register(MealMenu)
class MealMenuAdmin(admin.ModelAdmin):
    list_display = ('facility', 'day_of_week', 'meal', 'dishes')
    list_filter = ('facility', 'day_of_week', 'meal')


@admin.register(DietaryPreference)
class DietaryPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'preference', 'allergies')
    list_filter = ('preference',)
    search_fields = ('user__username', 'allergies')


@admin.register(MealReservation)
class MealReservationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'meal', 'dietary_choice')
