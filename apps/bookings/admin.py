from django.contrib import admin
from .models import Booking, BookingParticipant, BookingCancellation, BookingApproval


class BookingParticipantInline(admin.TabularInline):
    model = BookingParticipant
    extra = 0


class BookingApprovalInline(admin.TabularInline):
    model = BookingApproval
    extra = 0
    readonly_fields = ('action', 'action_by', 'comments', 'created_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference', 'facility', 'user', 'booking_date',
        'start_time', 'end_time', 'participant_count', 'status', 'payment_status', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'facility__category', 'booking_date')
    search_fields = ('booking_reference', 'user__username', 'facility__name', 'token', 'purpose')
    readonly_fields = ('booking_reference', 'token', 'qr_code', 'created_at', 'updated_at')
    date_hierarchy = 'booking_date'
    inlines = [BookingParticipantInline, BookingApprovalInline]


@admin.register(BookingCancellation)
class BookingCancellationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'cancelled_by', 'cancelled_at')
    readonly_fields = ('booking', 'cancelled_by', 'reason', 'cancelled_at')
