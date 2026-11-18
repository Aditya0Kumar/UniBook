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


# ---------------------------------------------------------------------------
# Phase 2: bad input must not cause server errors
# ---------------------------------------------------------------------------

class BadInputTests(TestCase):
    def setUp(self):
        make_fixture(self)
        self.admin = User.objects.create_superuser(
            username='reg_admin', email='reg_admin@test.edu', password='Password123!', role=User.ROLE_ADMIN,
        )

    def test_register_blank_fields(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': '', 'email': '', 'password': '', 'confirm_password': '', 'role': 'student',
        })
        self.assertEqual(response.status_code, 200)

    def test_register_duplicate_university_id(self):
        self.student.university_id = 'U-100'
        self.student.save()
        response = self.client.post(reverse('accounts:register'), {
            'username': 'dup', 'email': 'dup@test.edu', 'university_id': 'U-100',
            'password': 'Unusual-Pass-9481', 'confirm_password': 'Unusual-Pass-9481', 'role': 'student',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='dup').exists())

    def test_register_bad_department(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'deptx', 'email': 'deptx@test.edu', 'department': 'abc',
            'password': 'Unusual-Pass-9481', 'confirm_password': 'Unusual-Pass-9481', 'role': 'student',
        })
        self.assertEqual(response.status_code, 302)

    def test_booking_bad_participant_counts(self):
        self.client.force_login(self.student)
        url = reverse('bookings:booking_create', args=[self.facility.slug])
        before = Booking.objects.count()
        for value in ('abc', '-5', '0'):
            response = self.client.post(url, {
                'booking_date': (datetime.date.today() + datetime.timedelta(days=3)).isoformat(),
                'start_time': '10:00', 'end_time': '11:00', 'participant_count': value,
            })
            self.assertEqual(response.status_code, 302, value)
        self.assertEqual(Booking.objects.count(), before)

    def test_review_bad_ratings(self):
        from apps.reviews.models import Review
        self.client.force_login(self.student)
        url = reverse('reviews:submit_review', args=[self.facility.slug])
        for value in ('x', '99', '0'):
            self.assertEqual(self.client.post(url, {'rating': value}).status_code, 302, value)
        self.assertFalse(Review.objects.filter(user=self.student).exists())
        self.client.post(url, {'rating': '4'})
        self.assertEqual(Review.objects.get(user=self.student).rating, 4)

    def test_mess_menu_bad_facility_param(self):
        self.assertEqual(self.client.get('/mess/menu/?facility=abc').status_code, 200)

    def test_staff_approvals_bad_booking_id(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse('staff:approvals'), {'booking_id': 'abc', 'action': 'approve'})
        self.assertEqual(response.status_code, 302)

    def test_admin_panel_bad_ids_give_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_panel:facilities'), {'facility_id': 'abc', 'toggle_status': '1'})
        self.assertEqual(response.status_code, 404)

    def test_announcement_blank_fields(self):
        from apps.notifications.models import Announcement
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_panel:announcements'), {'action': 'create'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.exists())

    def test_maintenance_end_before_start(self):
        from apps.maintenance.models import FacilityMaintenance
        self.client.force_login(self.admin)
        self.client.post(reverse('admin_panel:maintenance'), {
            'action': 'create', 'facility_id': self.facility.id, 'title': 'Fix',
            'start_time': '2030-01-02T10:00', 'end_time': '2030-01-01T10:00',
        })
        self.assertFalse(FacilityMaintenance.objects.exists())


class FacilityApiCreateTests(APITestCase):
    def setUp(self):
        make_fixture(self)

    def test_manager_can_create_facility_with_category_id(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/facilities/', {
            'name': 'New Hall', 'description': 'd', 'building': 'B', 'category': self.category.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['category']['id'], self.category.id)

    def test_detail_still_returns_nested_category(self):
        response = self.client.get(f'/api/facilities/{self.facility.id}/')
        self.assertEqual(response.data['category']['slug'], 'courts')
