from django.contrib import admin
from .models import Review, Complaint


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('facility', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('facility__name', 'user__username', 'comment')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'facility', 'user', 'status', 'created_at', 'resolved_by')
    list_filter = ('status', 'facility')
    search_fields = ('title', 'facility__name', 'user__username', 'description')
