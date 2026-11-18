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

    def test_admin_can_create_facility_with_category_id(self):
        admin = User.objects.create_superuser(
            username='api_admin', email='api_admin@test.edu', password='Password123!', role=User.ROLE_ADMIN,
        )
        self.client.force_authenticate(admin)
        response = self.client.post('/api/facilities/', {
            'name': 'New Hall', 'description': 'd', 'building': 'B', 'category': self.category.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['category']['id'], self.category.id)

    def test_detail_still_returns_nested_category(self):
        response = self.client.get(f'/api/facilities/{self.facility.id}/')
        self.assertEqual(response.data['category']['slug'], 'courts')


# ---------------------------------------------------------------------------
# Phase 3: permissions and business rules
# ---------------------------------------------------------------------------

class PermissionAndRuleTests(APITestCase):
    def setUp(self):
        make_fixture(self)
        # A second manager who does NOT manage self.facility
        self.other_manager = User.objects.create_user(
            username='reg_manager2', email='reg_manager2@test.edu',
            password='Password123!', role=User.ROLE_FACILITY_MANAGER, is_staff=True,
        )
        self.booking.status = Booking.STATUS_PENDING
        self.booking.save()

    def test_other_manager_cannot_approve_via_staff_page(self):
        self.client.force_login(self.other_manager)
        self.client.post(reverse('staff:approvals'), {'booking_id': self.booking.id, 'action': 'approve'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)

    def test_assigned_manager_can_approve_via_staff_page(self):
        self.client.force_login(self.manager)
        self.client.post(reverse('staff:approvals'), {'booking_id': self.booking.id, 'action': 'approve'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)

    def test_other_manager_cannot_cancel(self):
        from django.core.exceptions import ValidationError
        from apps.bookings.services import cancel_booking
        with self.assertRaises(ValidationError):
            cancel_booking(self.booking, self.other_manager)

    def test_manager_cannot_approve_own_booking_elsewhere_via_api(self):
        own = Booking.objects.create(
            user=self.other_manager, facility=self.facility,
            booking_date=self.booking.booking_date, start_time=datetime.time(12, 0),
            end_time=datetime.time(13, 0), purpose='x', status=Booking.STATUS_PENDING,
        )
        self.client.force_authenticate(self.other_manager)
        response = self.client.post(f'/bookings/api/bookings/{own.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_managers_blocked_from_admin_panel(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse('admin_panel:facilities'), {'facility_id': self.facility.id, 'toggle_status': '1'})
        self.assertEqual(response.status_code, 302)
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.facility_status, Facility.STATUS_ACTIVE)

    def test_manager_can_only_edit_own_facility_via_api(self):
        self.client.force_authenticate(self.other_manager)
        denied = self.client.patch(f'/api/facilities/{self.facility.id}/', {'capacity': 99}, format='json')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.manager)
        allowed = self.client.patch(f'/api/facilities/{self.facility.id}/', {'capacity': 6}, format='json')
        self.assertEqual(allowed.status_code, 200)

    def test_exclusive_facility_enforces_capacity(self):
        from django.core.exceptions import ValidationError
        from apps.bookings.services import create_booking
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.student, facility_id=self.other_facility.id if self.other_facility.is_exclusive else self.facility.id,
                booking_date=self.booking.booking_date, start_time=datetime.time(14, 0),
                end_time=datetime.time(15, 0), participant_count=500,
            )

    def test_home_does_not_show_other_users_bookings(self):
        self.client.force_login(self.other_manager)
        response = self.client.get(reverse('public:home'))
        self.assertNotContains(response, self.booking.booking_reference)

    def test_invalid_complaint_status_rejected(self):
        from apps.reviews.models import Complaint
        admin = User.objects.create_superuser(username='c_admin', email='c_admin@test.edu', password='Password123!')
        complaint = Complaint.objects.create(facility=self.facility, user=self.student, title='t', description='d')
        self.client.force_login(admin)
        self.client.post(reverse('admin_panel:complaints'), {'complaint_id': complaint.id, 'status': 'bogus'})
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.STATUS_PENDING)


class PaymentRuleTests(TestCase):
    def setUp(self):
        make_fixture(self)
        self.facility.booking_price = 50
        self.facility.save()
        self.booking.payment_status = Booking.PAYMENT_PENDING
        self.booking.save()

    def test_cannot_pay_cancelled_booking(self):
        self.booking.status = Booking.STATUS_CANCELLED
        self.booking.save()
        self.client.force_login(self.student)
        self.client.post(reverse('payments:checkout', args=[self.booking.id]), {'payment_method': 'campus_card'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, Booking.PAYMENT_PENDING)

    def test_cancel_marks_payment_refunded(self):
        from apps.bookings.services import cancel_booking
        from apps.payments.models import Payment
        self.client.force_login(self.student)
        self.client.post(reverse('payments:checkout', args=[self.booking.id]), {'payment_method': 'campus_card'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, Booking.PAYMENT_PAID)
        cancel_booking(self.booking, self.student)
        self.assertEqual(Payment.objects.get(booking=self.booking).status, Payment.STATUS_REFUNDED)
        # A refunded booking cannot be paid again
        self.client.post(reverse('payments:checkout', args=[self.booking.id]), {'payment_method': 'campus_card'})
        self.assertEqual(Payment.objects.filter(booking=self.booking).count(), 1)

    def test_unpaid_booking_cannot_check_in(self):
        from apps.bookings.services import validate_and_checkin
        self.booking.booking_date = datetime.date.today()
        self.booking.save()
        result = validate_and_checkin(self.booking.booking_reference, self.manager)
        self.assertFalse(result['success'])
        self.assertIn('Payment Due', result['message'])


# ---------------------------------------------------------------------------
# Phase 4: cleanup
# ---------------------------------------------------------------------------

class CleanupTests(APITestCase):
    def setUp(self):
        make_fixture(self)

    def test_notifications_page_still_highlights_unread(self):
        from apps.notifications.models import Notification
        Notification.objects.create(recipient=self.student, title='Hello', message='m')
        self.client.force_login(self.student)
        first = self.client.get(reverse('notifications:list'))
        self.assertContains(first, 'bg-light px-3 rounded-2')
        self.assertFalse(Notification.objects.filter(recipient=self.student, is_read=False).exists())
        second = self.client.get(reverse('notifications:list'))
        self.assertNotContains(second, 'bg-light px-3 rounded-2')

    def test_diet_form_keeps_allergies(self):
        from apps.mess.models import DietaryPreference
        DietaryPreference.objects.create(user=self.student, preference='veg', allergies='Peanut')
        self.client.force_login(self.student)
        self.client.post(reverse('mess:menu'), {'update_diet': '1', 'preference': 'vegan'})
        pref = DietaryPreference.objects.get(user=self.student)
        self.assertEqual((pref.preference, pref.allergies), ('vegan', 'Peanut'))
        self.client.post(reverse('mess:menu'), {'update_diet': '1', 'preference': 'bogus', 'allergies': 'Gluten'})
        pref.refresh_from_db()
        self.assertEqual((pref.preference, pref.allergies), ('veg', 'Gluten'))

    def test_profile_rejects_non_image_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.student)
        fake = SimpleUploadedFile('x.png', b'not an image', content_type='image/png')
        self.client.post(reverse('accounts:profile'), {'first_name': 'S', 'profile_picture': fake})
        self.student.refresh_from_db()
        self.assertFalse(self.student.profile_picture)

    def test_profile_page_has_picture_field(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('accounts:profile')), 'name="profile_picture"')

    def test_user_api_is_admin_only(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get('/accounts/api/users/').status_code, status.HTTP_403_FORBIDDEN)
        admin = User.objects.create_superuser(username='u_admin', email='u_admin@test.edu', password='Password123!')
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get('/accounts/api/users/').status_code, 200)
        self.assertEqual(self.client.delete(f'/accounts/api/users/{self.student.id}/').status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_departments_api_is_public(self):
        self.assertEqual(self.client.get('/accounts/api/departments/').status_code, 200)

    def test_staff_dashboard_shows_staff_announcements(self):
        from apps.notifications.models import Announcement
        Announcement.objects.create(title='Staff briefing', content='c', target_role=Announcement.TARGET_STAFF, is_active=True)
        Announcement.objects.create(title='Students only', content='c', target_role=Announcement.TARGET_STUDENT, is_active=True)
        self.client.force_login(self.manager)
        response = self.client.get(reverse('staff:dashboard'))
        self.assertContains(response, 'Staff briefing')
        self.assertNotContains(response, 'Students only')

    def test_api_schema_generates(self):
        self.assertEqual(self.client.get('/api/schema/').status_code, 200)


# ---------------------------------------------------------------------------
# Final check
# ---------------------------------------------------------------------------

class FinalCheckTests(APITestCase):
    def setUp(self):
        make_fixture(self)

    def test_api_booking_for_missing_facility_is_400(self):
        self.client.force_authenticate(self.student)
        response = self.client.post('/bookings/api/bookings/', {
            'facility_id': 999999,
            'booking_date': (datetime.date.today() + datetime.timedelta(days=2)).isoformat(),
            'start_time': '10:00', 'end_time': '11:00',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_qr_scanner_does_not_render_messages_as_html(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('staff:qr_scanner'))
        self.assertNotContains(response, 'innerHTML')
        self.assertContains(response, 'textContent')
