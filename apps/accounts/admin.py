from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Details'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'university_id', 'department', 'is_active', 'is_staff'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'department')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'university_id')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('University Role & Academic Info', {
            'fields': ('role', 'university_id', 'department', 'phone_number', 'profile_picture')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('University Role & Academic Info', {
            'fields': ('role', 'university_id', 'department', 'phone_number', 'first_name', 'last_name', 'email')
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
