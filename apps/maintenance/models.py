from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.facilities.models import Facility


class FacilityMaintenance(models.Model):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, _('Scheduled')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='maintenance_records')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED, db_index=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    vendor_details = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = _('Facility Maintenance')
        verbose_name_plural = _('Facility Maintenance Records')

    def __str__(self):
        return f"{self.facility.name} - {self.title} ({self.get_status_display()})"
