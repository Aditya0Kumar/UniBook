from django.contrib import admin
from .models import FacilityCategory, Facility, FacilityImage, FacilityOperatingHour, Holiday


class FacilityOperatingHourInline(admin.TabularInline):
    model = FacilityOperatingHour
    extra = 0


class FacilityImageInline(admin.TabularInline):
    model = FacilityImage
    extra = 1


@admin.register(FacilityCategory)
class FacilityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'building', 'floor', 'capacity',
        'is_exclusive', 'booking_price', 'facility_status', 'approval_requirement', 'assigned_manager'
    )
    list_filter = ('category', 'facility_status', 'is_exclusive', 'campus', 'approval_requirement')
    search_fields = ('name', 'building', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FacilityOperatingHourInline, FacilityImageInline]


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_university_wide')
    list_filter = ('is_university_wide',)
    date_hierarchy = 'date'
    search_fields = ('name',)
