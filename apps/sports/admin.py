from django.contrib import admin
from .models import Sport, SportsCourt, SportsEquipment, SportsReservation


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_team_sport', 'players_per_side')


@admin.register(SportsCourt)
class SportsCourtAdmin(admin.ModelAdmin):
    list_display = ('facility', 'sport', 'court_number', 'surface_type', 'is_indoor')
    list_filter = ('sport', 'is_indoor')


@admin.register(SportsEquipment)
class SportsEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'total_quantity', 'available_quantity', 'rental_fee')
    list_filter = ('sport',)


@admin.register(SportsReservation)
class SportsReservationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'sport', 'court', 'is_team_booking')
