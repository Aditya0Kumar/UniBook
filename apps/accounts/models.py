from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return f"{self.name} ({self.code})"


class CustomUser(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_FACULTY = 'faculty'
    ROLE_FACILITY_MANAGER = 'facility_manager'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_STUDENT, _('Student')),
        (ROLE_FACULTY, _('Faculty Member')),
        (ROLE_FACILITY_MANAGER, _('Facility Manager')),
        (ROLE_ADMIN, _('Super Admin')),
    ]

    email = models.EmailField(_('Email Address'), unique=True)
    university_id = models.CharField(
        _('University ID / Roll Number'),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Unique university identification number or staff badge.')
    )
    role = models.CharField(
        _('User Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        db_index=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone_number = models.CharField(_('Phone Number'), max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    class Meta:
        ordering = ['username']
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} [{self.get_role_display()}]"

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_faculty(self):
        return self.role == self.ROLE_FACULTY

    @property
    def is_facility_manager(self):
        return self.role == self.ROLE_FACILITY_MANAGER or self.is_staff or self.is_superuser

    @property
    def is_superadmin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser


class UserProfile(models.Model):
    ACADEMIC_LEVELS = [
        ('undergraduate', 'Undergraduate Student'),
        ('postgraduate', 'Postgraduate Student'),
        ('phd', 'Doctoral Researcher / PhD'),
        ('faculty_member', 'Faculty Member'),
        ('staff_member', 'Campus Staff'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    academic_level = models.CharField(max_length=30, choices=ACADEMIC_LEVELS, blank=True)
    bio = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=50, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
