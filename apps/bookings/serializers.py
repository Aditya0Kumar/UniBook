import datetime
from rest_framework import serializers
from .models import Booking, BookingParticipant, BookingCancellation, BookingApproval
from apps.facilities.serializers import FacilityListSerializer


class BookingParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingParticipant
        fields = ['id', 'name', 'email', 'university_id', 'role']


class BookingSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    facility_category = serializers.CharField(source='facility.category.name', read_only=True)
    facility_building = serializers.CharField(source='facility.building', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    can_cancel = serializers.BooleanField(source='can_be_cancelled', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'token', 'user', 'user_name', 'user_email',
            'facility', 'facility_name', 'facility_category', 'facility_building',
            'booking_date', 'start_time', 'end_time', 'participant_count', 'purpose',
            'status', 'status_display', 'payment_status', 'payment_status_display',
            'qr_code', 'qr_code_url', 'approved_by', 'rejection_reason',
            'checked_in_at', 'checked_in_by', 'is_recurring', 'recurring_rule',
            'can_cancel', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'booking_reference', 'token', 'status', 'payment_status', 'qr_code',
            'approved_by', 'rejection_reason', 'checked_in_at', 'checked_in_by',
            'created_at', 'updated_at'
        ]

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
            return obj.qr_code.url
        return None


class BookingCreateSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    booking_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    participant_count = serializers.IntegerField(default=1, min_value=1)
    purpose = serializers.CharField(max_length=500, required=False, allow_blank=True)
    is_recurring = serializers.BooleanField(default=False)
    recurring_rule = serializers.CharField(max_length=50, required=False, allow_blank=True)


class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class BookingApprovalActionSerializer(serializers.Serializer):
    comments = serializers.CharField(max_length=500, required=False, allow_blank=True)


class QRCheckInSerializer(serializers.Serializer):
    token_or_reference = serializers.CharField(max_length=200)
