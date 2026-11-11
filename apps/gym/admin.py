from django.contrib import admin
from .models import Trainer, GymSession, GymMembership, GymReservation


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'specialization')


@admin.register(GymSession)
class GymSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'facility', 'session_type', 'start_time', 'end_time', 'capacity', 'trainer')
    list_filter = ('session_type', 'facility')


@admin.register(GymMembership)
class GymMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active')
    search_fields = ('user__username',)


@admin.register(GymReservation)
class GymReservationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'session', 'trainer')
