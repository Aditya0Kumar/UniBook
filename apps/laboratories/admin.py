from django.contrib import admin
from .models import Laboratory, LabEquipment, LabReservationDetail


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ('facility', 'lab_type', 'safety_level', 'requires_lab_coat', 'supervisor')
    list_filter = ('lab_type', 'requires_lab_coat')


@admin.register(LabEquipment)
class LabEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'laboratory', 'model_number', 'total_count', 'available_count', 'is_operational')
    list_filter = ('is_operational',)


@admin.register(LabReservationDetail)
class LabReservationDetailAdmin(admin.ModelAdmin):
    list_display = ('booking', 'course_code', 'project_title', 'supervisor_faculty')
