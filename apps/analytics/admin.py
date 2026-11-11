from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'resource_type', 'resource_id', 'ip_address')
    list_filter = ('action', 'resource_type')
    search_fields = ('user__username', 'action', 'details', 'resource_id')
    readonly_fields = ('timestamp', 'user', 'action', 'resource_type', 'resource_id', 'ip_address', 'details')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
