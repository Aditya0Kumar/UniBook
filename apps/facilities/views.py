import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsFacilityManagerOrAdmin
from apps.bookings.services import calculate_facility_slots
from apps.bookings.models import Booking
from apps.reviews.models import Review
from apps.notifications.models import Announcement
from .models import Facility, FacilityCategory, FacilityImage, FacilityOperatingHour, Holiday
from .serializers import (
    FacilityListSerializer,
    FacilityDetailSerializer,
    FacilityCategorySerializer,
    HolidaySerializer
)


# -------------------------------------------------------------
# Template Views (Public & Discovery)
# -------------------------------------------------------------

def home_view(request):
    categories = FacilityCategory.objects.annotate(fac_count=Count('facilities')).all()
    featured_facilities = Facility.objects.filter(
        facility_status=Facility.STATUS_ACTIVE
    ).select_related('category')[:8]

    # Specific 4 showcase facility categories matching top university demands
    showcase_facilities = [
        {
            'title': 'Seminar Hall',
            'sub': 'Events • Presentations • Workshops',
            'icon': 'presentation',
            'status_label': 'Available',
            'status_color': 'success',
            'image': 'facilities/seminar-hall-101.jpg',
            'facility': Facility.objects.filter(category__slug='seminar-hall').first()
        },
        {
            'title': 'Computer Lab',
            'sub': 'Coding • Research • Training',
            'icon': 'laptop',
            'status_label': 'Available',
            'status_color': 'success',
            'image': 'facilities/advanced-ai-cloud-lab.jpg',
            'facility': Facility.objects.filter(category__slug='computer-laboratory').first()
        },
        {
            'title': 'Sports Ground',
            'sub': 'Football • Cricket • Athletics',
            'icon': 'activity',
            'status_label': 'Available',
            'status_color': 'success',
            'image': 'facilities/main-campus-football-stadium.jpg',
            'facility': Facility.objects.filter(category__slug='sports').first()
        },
        {
            'title': 'Auditorium',
            'sub': 'Conferences • Cultural Events',
            'icon': 'armchair',
            'status_label': 'Limited',
            'status_color': 'warning',
            'image': 'facilities/kalam-memorial-auditorium.jpg',
            'facility': Facility.objects.filter(category__slug='auditorium').first()
        },
    ]

    # User active bookings or sample demo upcoming booking for visual showcase
    user_bookings = []
    if request.user.is_authenticated:
        user_bookings = Booking.objects.filter(
            user=request.user
        ).select_related('facility').order_by('-booking_date', '-start_time')[:3]

    if not user_bookings:
        user_bookings = Booking.objects.select_related('facility').order_by('-booking_date', '-start_time')[:2]

    total_facilities = Facility.objects.count()
    total_bookings = Booking.objects.count()
    announcements = Announcement.objects.filter(is_active=True)[:4]

    context = {
        'categories': categories,
        'featured_facilities': featured_facilities,
        'showcase_facilities': showcase_facilities,
        'user_bookings': user_bookings,
        'total_facilities': total_facilities,
        'total_bookings': total_bookings,
        'announcements': announcements,
    }
    return render(request, 'public/home.html', context)


def about_view(request):
    return render(request, 'public/about.html')


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Thank you! Your message has been received by Campus Support.")
        return redirect('public:contact')
    return render(request, 'public/contact.html')


def facility_directory_view(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    campus = request.GET.get('campus', '').strip()
    price_filter = request.GET.get('pricing', '').strip()
    sort = request.GET.get('sort', 'name')

    facilities = Facility.objects.filter(
        facility_status=Facility.STATUS_ACTIVE
    ).select_related('category')

    if query:
        facilities = facilities.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(building__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        facilities = facilities.filter(category__slug=category_slug)

    if campus:
        facilities = facilities.filter(campus__iexact=campus)

    if price_filter == 'free':
        facilities = facilities.filter(booking_price=0)
    elif price_filter == 'paid':
        facilities = facilities.filter(booking_price__gt=0)

    if sort == 'capacity':
        facilities = facilities.order_by('-capacity')
    elif sort == 'rating':
        facilities = facilities.annotate(avg_r=Avg('reviews__rating')).order_by('-avg_r')
    else:
        facilities = facilities.order_by('name')

    categories = FacilityCategory.objects.all()
    campuses = Facility.objects.values_list('campus', flat=True).distinct()

    context = {
        'facilities': facilities,
        'categories': categories,
        'campuses': campuses,
        'selected_category': category_slug,
        'selected_campus': campus,
        'search_query': query,
        'selected_sort': sort,
        'selected_pricing': price_filter,
    }
    return render(request, 'public/directory.html', context)


def facility_detail_view(request, slug):
    facility = get_object_or_404(
        Facility.objects.select_related('category', 'assigned_manager'),
        slug=slug
    )
    operating_hours = facility.operating_hours.all()
    reviews = facility.reviews.filter(is_approved=True).select_related('user')[:10]
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(facility=facility, user=request.user).first()

    today_str = timezone.localdate().strftime('%Y-%m-%d')
    max_date_str = (timezone.localdate() + datetime.timedelta(days=facility.max_advance_booking_days)).strftime('%Y-%m-%d')

    context = {
        'facility': facility,
        'operating_hours': operating_hours,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'user_review': user_review,
        'today_str': today_str,
        'max_date_str': max_date_str,
    }
    return render(request, 'public/facility_detail.html', context)


# -------------------------------------------------------------
# REST API ViewSets & Endpoints
# -------------------------------------------------------------

class FacilityCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FacilityCategory.objects.all()
    serializer_class = FacilityCategorySerializer
    permission_classes = [permissions.AllowAny]


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().select_related('category', 'assigned_manager')
    filterset_fields = ['category__slug', 'campus', 'facility_status', 'approval_requirement']
    search_fields = ['name', 'description', 'building', 'campus']
    ordering_fields = ['name', 'capacity', 'booking_price', 'created_at']

    def get_serializer_class(self):
        if self.action in ['list']:
            return FacilityListSerializer
        return FacilityDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsFacilityManagerOrAdmin()]
        return [permissions.AllowAny()]


class FacilityAvailabilityAPIView(APIView):
    """
    Returns calculated slot availability for a facility on a specific date.
    Query param: ?date=YYYY-MM-DD
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        facility = get_object_or_404(Facility, pk=pk)
        date_str = request.query_params.get('date')
        if not date_str:
            target_date = timezone.localdate()
        else:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        slots = calculate_facility_slots(facility, target_date)
        return Response({
            'facility_id': facility.id,
            'facility_name': facility.name,
            'date': target_date.strftime('%Y-%m-%d'),
            'capacity': facility.capacity,
            'is_exclusive': facility.is_exclusive,
            'slots': slots
        })


class FacilityCalendarEventsAPIView(APIView):
    """
    Returns events in FullCalendar format for a given date range.
    Query params: ?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        facility = get_object_or_404(Facility, pk=pk)
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')

        now = timezone.localdate()
        start_date = now - datetime.timedelta(days=7)
        end_date = now + datetime.timedelta(days=30)

        if start_str:
            try:
                start_date = datetime.datetime.strptime(start_str[:10], '%Y-%m-%d').date()
            except ValueError:
                pass
        if end_str:
            try:
                end_date = datetime.datetime.strptime(end_str[:10], '%Y-%m-%d').date()
            except ValueError:
                pass

        bookings = Booking.objects.filter(
            facility=facility,
            booking_date__gte=start_date,
            booking_date__lte=end_date,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING, Booking.STATUS_CHECKED_IN]
        ).select_related('user')

        events = []
        for b in bookings:
            start_iso = f"{b.booking_date}T{b.start_time.strftime('%H:%M:%S')}"
            end_iso = f"{b.booking_date}T{b.end_time.strftime('%H:%M:%S')}"
            
            color = '#2563EB' # Blue for confirmed
            if b.status == Booking.STATUS_PENDING:
                color = '#F59E0B' # Amber for pending
            elif b.status == Booking.STATUS_CHECKED_IN:
                color = '#10B981' # Green for checked in

            title = f"Reserved: {b.purpose[:20]}" if b.purpose else "Reserved"
            if request.user.is_authenticated and (request.user.is_facility_manager or request.user.is_superadmin):
                title = f"{b.user.get_full_name() or b.user.username} - {title}"

            events.append({
                'id': b.id,
                'title': title,
                'start': start_iso,
                'end': end_iso,
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'reference': b.booking_reference,
                    'status': b.get_status_display(),
                    'participants': b.participant_count
                }
            })

        return Response(events)
