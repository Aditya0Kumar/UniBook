from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility
from apps.bookings.models import Booking


class Laboratory(models.Model):
    LAB_COMPUTER = 'computer'
    LAB_RESEARCH = 'research'
    LAB_PHYSICS = 'physics'
    LAB_CHEMISTRY = 'chemistry'
    LAB_ROBOTICS = 'robotics'
    LAB_BIO = 'bio'

    LAB_TYPES = [
        (LAB_COMPUTER, _('Computer Laboratory')),
        (LAB_RESEARCH, _('Research & Innovation Lab')),
        (LAB_PHYSICS, _('Physics & Materials Lab')),
        (LAB_CHEMISTRY, _('Chemistry & Wet Lab')),
        (LAB_ROBOTICS, _('Robotics & Automation Lab')),
        (LAB_BIO, _('Biotechnology & Life Sciences Lab')),
    ]

    facility = models.OneToOneField(Facility, on_delete=models.CASCADE, related_name='lab_profile')
    lab_type = models.CharField(max_length=30, choices=LAB_TYPES, default=LAB_COMPUTER)
    safety_level = models.CharField(max_length=50, default='Level 1 (Standard General Safety)')
    safety_guidelines = models.TextField(blank=True)
    requires_lab_coat = models.BooleanField(default=False)
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_labs')

    def __str__(self):
        return f"{self.facility.name} [{self.get_lab_type_display()}]"


class LabEquipment(models.Model):
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, related_name='equipment_list')
    name = models.CharField(max_length=150)
    model_number = models.CharField(max_length=100, blank=True)
    serial_code = models.CharField(max_length=100, blank=True)
    total_count = models.PositiveIntegerField(default=1)
    available_count = models.PositiveIntegerField(default=1)
    is_operational = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.laboratory.facility.name})"


class LabReservationDetail(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='lab_details')
    course_code = models.CharField(max_length=50, blank=True, help_text=_('e.g. CS401, CHEM202'))
    supervisor_faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    project_title = models.CharField(max_length=200, blank=True)
    special_chemical_hazards = models.TextField(blank=True)
    equipment_requested = models.ManyToManyField(LabEquipment, blank=True, related_name='reservations')

    def __str__(self):
        return f"Lab Detail for {self.booking.booking_reference}"
