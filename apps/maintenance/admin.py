from django.contrib import admin
from .models import FacilityMaintenance


@admin.register(FacilityMaintenance)
class FacilityMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('facility', 'title', 'start_time', 'end_time', 'status', 'created_by')
    list_filter = ('status', 'facility')
    search_fields = ('facility__name', 'title', 'description')
