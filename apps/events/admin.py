from django.contrib import admin
from .models import EventAuditoriumDetail, EventBookingDetail


@admin.register(EventAuditoriumDetail)
class EventAuditoriumDetailAdmin(admin.ModelAdmin):
    list_display = ('facility', 'stage_size', 'green_rooms_count', 'has_recording_equipment')


@admin.register(EventBookingDetail)
class EventBookingDetailAdmin(admin.ModelAdmin):
    list_display = ('booking', 'event_title', 'event_type', 'expected_attendees', 'faculty_coordinator')
    list_filter = ('event_type',)
