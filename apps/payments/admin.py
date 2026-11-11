from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'booking', 'user', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('transaction_id', 'booking__booking_reference', 'user__username')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'payment', 'amount', 'processed_by', 'created_at')
