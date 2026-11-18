import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsOwnerOrStaff, IsFacilityManagerOrAdmin
from apps.facilities.models import Facility
from .models import Booking, BookingParticipant, BookingCancellation
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingCancelSerializer,
    BookingApprovalActionSerializer,
    QRCheckInSerializer
)
from .services import (
    create_booking,
    cancel_booking,
    approve_booking,
    reject_booking,
    validate_and_checkin
)


# -------------------------------------------------------------
# Template Views
# -------------------------------------------------------------

@login_required
def booking_create_view(request, slug):
    facility = get_object_or_404(Facility, slug=slug)

    if request.method == 'POST':
        date_str = request.POST.get('booking_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        participant_count = int(request.POST.get('participant_count', 1))
        purpose = request.POST.get('purpose', '').strip()
        is_recurring = request.POST.get('is_recurring') == 'on'
        recurring_rule = request.POST.get('recurring_rule', '')

        try:
            booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date or time format.")
            return redirect('public:facility_detail', slug=facility.slug)

        ip_address = request.META.get('REMOTE_ADDR')

        try:
            booking = create_booking(
                user=request.user,
                facility_id=facility.id,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                participant_count=participant_count,
                purpose=purpose,
                is_recurring=is_recurring,
                recurring_rule=recurring_rule,
                ip_address=ip_address
            )
            messages.success(
                request,
                f"Booking reserved! Reference: {booking.booking_reference}. "
                f"Status: {booking.get_status_display()}."
            )
            return redirect('bookings:booking_detail', pk=booking.id)
        except ValidationError as e:
            messages.error(request, f"Booking failed: {e.message if hasattr(e, 'message') else str(e)}")
            return redirect('public:facility_detail', slug=facility.slug)

    return redirect('public:facility_detail', slug=facility.slug)


@login_required
def my_bookings_view(request):
    user = request.user
    status_filter = request.GET.get('status', 'all')
    
    bookings = Booking.objects.filter(user=user).select_related('facility', 'facility__category')

    now_date = timezone.localdate()

    if status_filter == 'upcoming':
        bookings = bookings.filter(
            booking_date__gte=now_date,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
        )
    elif status_filter == 'past':
        bookings = bookings.filter(
            booking_date__lt=now_date
        )
    elif status_filter == 'pending':
        bookings = bookings.filter(status=Booking.STATUS_PENDING)
    elif status_filter == 'completed':
        bookings = bookings.filter(status__in=[Booking.STATUS_COMPLETED, Booking.STATUS_CHECKED_IN])
    elif status_filter == 'cancelled':
        bookings = bookings.filter(status=Booking.STATUS_CANCELLED)

    context = {
        'bookings': bookings,
        'current_status': status_filter,
    }
    return render(request, 'student/my_bookings.html', context)


@login_required
def booking_detail_view(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('facility', 'facility__category', 'user', 'approved_by'),
        pk=pk
    )

    # Check permission
    if booking.user != request.user and not (request.user.is_facility_manager or request.user.is_superadmin):
        messages.error(request, "You are not authorized to view this booking.")
        return redirect('student:dashboard')

    context = {
        'booking': booking,
    }
    return render(request, 'student/booking_detail.html', context)


@login_required
def booking_cancel_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'User cancelled from dashboard')
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            cancel_booking(booking, request.user, reason=reason, ip_address=ip_address)
            messages.success(request, f"Booking {booking.booking_reference} has been cancelled successfully.")
        except ValidationError as e:
            messages.error(request, f"Cancellation failed: {e.message if hasattr(e, 'message') else str(e)}")

    return redirect('bookings:booking_detail', pk=booking.id)


# -------------------------------------------------------------
# REST API ViewSet
# -------------------------------------------------------------

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'payment_status', 'facility', 'booking_date']
    search_fields = ['booking_reference', 'purpose', 'user__username', 'facility__name']
    ordering_fields = ['booking_date', 'start_time', 'created_at']
    # Bookings are created through create_booking() and changed only through the
    # cancel / approve / reject / check-in actions, so every change goes through the
    # booking rules. Generic PUT/PATCH/DELETE would bypass them.
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Booking.objects.none()
        user = self.request.user
        if user.is_superadmin:
            return Booking.objects.all().select_related('facility', 'user', 'facility__category')
        elif user.is_facility_manager:
            # Managed facilities + own bookings
            return Booking.objects.filter(
                Q(facility__assigned_manager=user) | Q(user=user)
            ).select_related('facility', 'user', 'facility__category')
        else:
            return Booking.objects.filter(user=user).select_related('facility', 'user', 'facility__category')

    def create(self, request, *args, **kwargs):
        create_ser = BookingCreateSerializer(data=request.data)
        create_ser.is_valid(raise_exception=True)
        data = create_ser.validated_data

        ip_address = request.META.get('REMOTE_ADDR')

        try:
            booking = create_booking(
                user=request.user,
                facility_id=data['facility_id'],
                booking_date=data['booking_date'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                participant_count=data.get('participant_count', 1),
                purpose=data.get('purpose', ''),
                is_recurring=data.get('is_recurring', False),
                recurring_rule=data.get('recurring_rule', ''),
                ip_address=ip_address
            )
            serializer = BookingSerializer(booking, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related('facility', 'facility__category')
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = BookingSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = BookingSerializer(bookings, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        ser = BookingCancelSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reason = ser.validated_data.get('reason', '')
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            cancelled = cancel_booking(booking, request.user, reason=reason, ip_address=ip_address)
            return Response(BookingSerializer(cancelled, context={'request': request}).data)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsFacilityManagerOrAdmin])
    def approve(self, request, pk=None):
        booking = self.get_object()
        ser = BookingApprovalActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        comments = ser.validated_data.get('comments', '')
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            approved = approve_booking(booking, request.user, comments=comments, ip_address=ip_address)
            return Response(BookingSerializer(approved, context={'request': request}).data)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsFacilityManagerOrAdmin])
    def reject(self, request, pk=None):
        booking = self.get_object()
        ser = BookingApprovalActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        comments = ser.validated_data.get('comments', '')
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            rejected = reject_booking(booking, request.user, reason=comments, ip_address=ip_address)
            return Response(BookingSerializer(rejected, context={'request': request}).data)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='check-in', permission_classes=[IsFacilityManagerOrAdmin])
    def check_in(self, request):
        ser = QRCheckInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token_or_ref = ser.validated_data['token_or_reference']
        ip_address = request.META.get('REMOTE_ADDR')

        res = validate_and_checkin(token_or_ref, request.user, ip_address=ip_address)
        if not res['success']:
            return Response(
                {
                    'success': False,
                    'message': res['message'],
                    'booking': BookingSerializer(res['booking'], context={'request': request}).data if res['booking'] else None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'success': True,
            'message': res['message'],
            'booking': BookingSerializer(res['booking'], context={'request': request}).data
        })
