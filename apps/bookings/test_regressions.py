"""Regression tests for bugs found in the November 2026 code review (phase 1)."""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.facilities.models import Facility, FacilityCategory

User = get_user_model()


def make_fixture(test):
    test.student = User.objects.create_user(
        username='reg_student', email='reg_student@test.edu',
        password='Password123!', role=User.ROLE_STUDENT,
    )
    test.manager = User.objects.create_user(
        username='reg_manager', email='reg_manager@test.edu',
        password='Password123!', role=User.ROLE_FACILITY_MANAGER, is_staff=True,
    )
    test.category = FacilityCategory.objects.create(name='Courts', slug='courts')
    test.facility = Facility.objects.create(
        name='Court A', category=test.category, description='d', building='B',
        capacity=4, is_exclusive=True, assigned_manager=test.manager,
    )
    test.other_facility = Facility.objects.create(
        name='Court B', category=test.category, description='d', building='B', capacity=4,
    )
    test.booking = Booking.objects.create(
        user=test.student, facility=test.facility,
        booking_date=datetime.date.today() + datetime.timedelta(days=2),
        start_time=datetime.time(10, 0), end_time=datetime.time(11, 0),
        participant_count=1, purpose='Practice',
    )


class HomePageTests(TestCase):
    def setUp(self):
        make_fixture(self)

    def test_home_renders_for_logged_in_user_with_bookings(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('public:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('bookings:booking_detail', args=[self.booking.id]))


class RegistrationRoleTests(APITestCase):
    def test_api_register_rejects_admin_role(self):
        response = self.client.post(reverse('accounts:api_register'), {
            'username': 'sneaky', 'email': 'sneaky@test.edu',
            'password': 'Unusual-Pass-9481', 'confirm_password': 'Unusual-Pass-9481',
            'role': User.ROLE_ADMIN,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='sneaky').exists())

    def test_api_register_rejects_weak_password(self):
        response = self.client.post(reverse('accounts:api_register'), {
            'username': 'weak', 'email': 'weak@test.edu',
            'password': '123456', 'confirm_password': '123456',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_register_student_still_works(self):
        response = self.client.post(reverse('accounts:api_register'), {
            'username': 'newbie', 'email': 'newbie@test.edu',
            'password': 'Unusual-Pass-9481', 'confirm_password': 'Unusual-Pass-9481',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username='newbie').role, User.ROLE_STUDENT)

    def test_form_register_rejects_privileged_roles(self):
        for role in (User.ROLE_ADMIN, User.ROLE_FACILITY_MANAGER):
            self.client.post(reverse('accounts:register'), {
                'username': f'form_{role}', 'email': f'{role}@test.edu',
                'password': 'Unusual-Pass-9481', 'confirm_password': 'Unusual-Pass-9481',
                'role': role,
            })
            self.assertFalse(User.objects.filter(username=f'form_{role}').exists(), role)

    def test_form_register_rejects_weak_password(self):
        self.client.post(reverse('accounts:register'), {
            'username': 'weakform', 'email': 'weakform@test.edu',
            'password': 'a', 'confirm_password': 'a', 'role': User.ROLE_STUDENT,
        })
        self.assertFalse(User.objects.filter(username='weakform').exists())


class LoginRedirectTests(TestCase):
    def setUp(self):
        make_fixture(self)

    def test_external_next_is_ignored(self):
        response = self.client.post(
            reverse('accounts:login') + '?next=https://evil.example/',
            {'username': 'reg_student', 'password': 'Password123!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('student:dashboard'))

    def test_internal_next_is_followed(self):
        response = self.client.post(
            reverse('accounts:login') + '?next=/bookings/my/',
            {'username': 'reg_student', 'password': 'Password123!'},
        )
        self.assertEqual(response['Location'], '/bookings/my/')


class BookingApiTests(APITestCase):
    def setUp(self):
        make_fixture(self)

    def test_manager_can_list_bookings(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get('/bookings/api/bookings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_owner_cannot_patch_or_delete_booking(self):
        self.client.force_authenticate(self.student)
        url = f'/bookings/api/bookings/{self.booking.id}/'
        patch = self.client.patch(url, {'facility': self.other_facility.id, 'participant_count': 999}, format='json')
        delete = self.client.delete(url)
        self.assertEqual(patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.facility_id, self.facility.id)
        self.assertEqual(self.booking.participant_count, 1)

    def test_owner_can_still_cancel_via_action(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(f'/bookings/api/bookings/{self.booking.id}/cancel/', {'reason': 'x'})
        self.assertEqual(response.status_code, 200)


class QrScannerTests(TestCase):
    def setUp(self):
        make_fixture(self)

    def test_scanner_page_posts_to_real_check_in_endpoint(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('staff:qr_scanner'))
        check_in_url = reverse('bookings:booking-api-check-in')
        self.assertEqual(check_in_url, '/bookings/api/bookings/check-in/')
        self.assertContains(response, f"fetch('{check_in_url}'")
