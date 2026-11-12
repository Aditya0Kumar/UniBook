from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import datetime


class FacilityCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='building', help_text=_('Lucide icon name (e.g. dumbbell, utensils, trophy, monitor)'))
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Facility Category')
        verbose_name_plural = _('Facility Categories')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Facility(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Active')),
        (STATUS_INACTIVE, _('Inactive')),
        (STATUS_MAINTENANCE, _('Under Maintenance')),
        (STATUS_CLOSED, _('Temporarily Closed')),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    category = models.ForeignKey(
        FacilityCategory,
        on_delete=models.PROTECT,
        related_name='facilities'
    )
    description = models.TextField()
    image = models.ImageField(upload_to='facilities/', null=True, blank=True)
    campus = models.CharField(max_length=100, default='Main Campus')
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=50, default='Ground Floor')
    room_number = models.CharField(max_length=50, blank=True)
    location_details = models.TextField(blank=True, help_text=_('Directions or specific landmark details.'))
    
    capacity = models.PositiveIntegerField(
        default=30,
        help_text=_('Maximum simultaneous capacity or audience seating.')
    )
    is_exclusive = models.BooleanField(
        default=True,
        help_text=_('Exclusive: 1 reservation reserves the entire room/hall/court. Shared: multiple individual users can reserve slots up to capacity (e.g. Gym, Mess).')
    )

    # Operating Rules
    opening_time = models.TimeField(default=datetime.time(8, 0))
    closing_time = models.TimeField(default=datetime.time(22, 0))
    available_days = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of integers 0-6 (0=Monday, 6=Sunday). Empty means Mon-Sun (all days).')
    )
    slot_duration = models.PositiveIntegerField(
        default=60,
        help_text=_('Standard booking slot duration in minutes (e.g. 30, 60, 90).')
    )
    booking_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text=_('Fee per slot (0.00 for free university facilities).')
    )
    min_booking_duration = models.PositiveIntegerField(
        default=30,
        help_text=_('Minimum duration in minutes.')
    )
    max_booking_duration = models.PositiveIntegerField(
        default=180,
        help_text=_('Maximum duration in minutes per reservation.')
    )
    max_advance_booking_days = models.PositiveIntegerField(
        default=14,
        help_text=_('How many days in advance users can book.')
    )
    cancellation_deadline = models.PositiveIntegerField(
        default=2,
        help_text=_('Hours before booking start time when cancellations are permitted.')
    )
    approval_requirement = models.BooleanField(
        default=False,
        help_text=_('If true, bookings require manager/admin confirmation.')
    )
    assigned_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_facilities',
        help_text=_('Facility Manager responsible for this facility.')
    )
    facility_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = _('Facility')
        verbose_name_plural = _('Facilities')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Facility.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @property
    def is_available_for_booking(self):
        return self.facility_status == self.STATUS_ACTIVE

    @property
    def is_free(self):
        return self.booking_price <= 0

    @property
    def display_image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        FALLBACK_URLS = {
            'campus-central-gymnasium': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1200&q=80',
            'north-dining-hall-mess': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80',
            'south-annex-dining-complex': 'https://images.unsplash.com/photo-1567521464027-f127ff144326?auto=format&fit=crop&w=1200&q=80',
            'badminton-court-1': 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=1200&q=80',
            'badminton-court-2': 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=1200&q=80',
            'badminton-court-3': 'https://images.unsplash.com/photo-1599474924187-334a4ae5bd3c?auto=format&fit=crop&w=1200&q=80',
            'basketball-court-a-arena': 'https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=1200&q=80',
            'basketball-court-b-outdoor': 'https://images.unsplash.com/photo-1519861531473-9200262188bf?auto=format&fit=crop&w=1200&q=80',
            'main-campus-football-stadium': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=1200&q=80',
            'olympic-aquatics-complex': 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1200&q=80',
            'advanced-ai-cloud-lab': 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80',
            'robotics-cps-lab': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80',
            'nanotech-materials-lab': 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=1200&q=80',
            'kalam-memorial-auditorium': 'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&w=1200&q=80',
            'raman-science-auditorium': 'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1200&q=80',
            'seminar-hall-101': 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80',
            'seminar-hall-202': 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80',
            'deans-executive-seminar-room': 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&w=1200&q=80',
            'library-discussion-pod-a': 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1200&q=80',
            'digital-media-research-pod-b': 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=1200&q=80',
        }
        return FALLBACK_URLS.get(self.slug, 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80')


class FacilityImage(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='facilities/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"Image for {self.facility.name} ({self.caption or 'No caption'})"


class FacilityOperatingHour(models.Model):
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='operating_hours')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('facility', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK).get(self.day_of_week, '')
        if self.is_closed:
            return f"{self.facility.name} - {day_name}: Closed"
        return f"{self.facility.name} - {day_name}: {self.opening_time} - {self.closing_time}"


class Holiday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_university_wide = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        verbose_name = _('Holiday')
        verbose_name_plural = _('Holidays')

    def __str__(self):
        return f"{self.name} ({self.date})"
