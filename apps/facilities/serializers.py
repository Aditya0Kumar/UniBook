from rest_framework import serializers
from django.db.models import Avg
from .models import FacilityCategory, Facility, FacilityImage, FacilityOperatingHour, Holiday


class FacilityCategorySerializer(serializers.ModelSerializer):
    facility_count = serializers.IntegerField(source='facilities.count', read_only=True)

    class Meta:
        model = FacilityCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'facility_count']


class FacilityImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityImage
        fields = ['id', 'image', 'caption', 'is_primary']


class FacilityOperatingHourSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = FacilityOperatingHour
        fields = ['id', 'day_of_week', 'day_name', 'opening_time', 'closing_time', 'is_closed']


class FacilityListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'category_icon',
            'image', 'campus', 'building', 'floor', 'room_number', 'capacity',
            'is_exclusive', 'booking_price', 'facility_status', 'approval_requirement',
            'average_rating'
        ]

    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 5.0


class FacilityDetailSerializer(serializers.ModelSerializer):
    category = FacilityCategorySerializer(read_only=True)
    gallery_images = FacilityImageSerializer(many=True, read_only=True)
    operating_hours = FacilityOperatingHourSerializer(many=True, read_only=True)
    manager_name = serializers.CharField(source='assigned_manager.get_full_name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'slug', 'category', 'description', 'image',
            'campus', 'building', 'floor', 'room_number', 'location_details',
            'capacity', 'is_exclusive', 'opening_time', 'closing_time',
            'available_days', 'slot_duration', 'booking_price',
            'min_booking_duration', 'max_booking_duration', 'max_advance_booking_days',
            'cancellation_deadline', 'approval_requirement', 'assigned_manager',
            'manager_name', 'facility_status', 'gallery_images', 'operating_hours',
            'average_rating', 'reviews_count', 'created_at', 'updated_at'
        ]

    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 5.0

    def get_reviews_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'name', 'date', 'description', 'is_university_wide']
