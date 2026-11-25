from django import forms
from django.contrib.auth import get_user_model
from apps.facilities.models import Facility, FacilityCategory

User = get_user_model()

DAY_CHOICES = (
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
)


class FacilityForm(forms.ModelForm):
    available_days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text='Select the operating days for this facility. Leave empty to allow all days (Mon-Sun).'
    )

    class Meta:
        model = Facility
        fields = [
            'name',
            'category',
            'description',
            'image',
            'campus',
            'building',
            'floor',
            'room_number',
            'location_details',
            'capacity',
            'is_exclusive',
            'facility_status',
            'opening_time',
            'closing_time',
            'available_days',
            'slot_duration',
            'booking_price',
            'min_booking_duration',
            'max_booking_duration',
            'max_advance_booking_days',
            'cancellation_deadline',
            'approval_requirement',
            'assigned_manager',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Innovation Hall'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description of the facility and equipment...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'campus': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Campus'}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science Complex Block A'}),
            'floor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2nd Floor'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Room 204'}),
            'location_details': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Near West Staircase'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_exclusive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'facility_status': forms.Select(attrs={'class': 'form-select'}),
            'opening_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'booking_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'min_booking_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'max_booking_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'max_advance_booking_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cancellation_deadline': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'approval_requirement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assigned_manager': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_manager queryset to staff / managers / superusers
        self.fields['assigned_manager'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
        self.fields['assigned_manager'].empty_label = "— Unassigned (Admin Only) —"

        # Populate available_days if instance exists
        if self.instance and self.instance.pk:
            if isinstance(self.instance.available_days, list):
                self.initial['available_days'] = [str(d) for d in self.instance.available_days]

    def clean_available_days(self):
        data = self.cleaned_data.get('available_days')
        if not data:
            return []
        return [int(d) for d in data]

    def clean(self):
        cleaned_data = super().clean()
        opening = cleaned_data.get('opening_time')
        closing = cleaned_data.get('closing_time')
        min_dur = cleaned_data.get('min_booking_duration')
        max_dur = cleaned_data.get('max_booking_duration')

        if opening and closing and closing <= opening:
            self.add_error('closing_time', 'Closing time must be after opening time.')

        if min_dur and max_dur and max_dur < min_dur:
            self.add_error('max_booking_duration', 'Maximum booking duration cannot be less than minimum booking duration.')

        return cleaned_data
