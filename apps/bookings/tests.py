import datetime
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.accounts.models import Department
from apps.facilities.models import FacilityCategory, Facility, FacilityOperatingHour, Holiday
from apps.bookings.models import Booking
from apps.bookings.services import (
    create_booking,
    cancel_booking,
    approve_booking,
    reject_booking,
    validate_and_checkin,
    calculate_facility_slots
)

User = get_user_model()


class UniBookBookingEngineTests(TestCase):
    def setUp(self):
        # Create department
        self.dept = Department.objects.create(name="Computer Science", code="CS")

        # Create student user
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.edu',
            password='Password123!',
            role=User.ROLE_STUDENT,
            university_id='STU001',
            department=self.dept
        )

        # Create second student user
        self.student2 = User.objects.create_user(
            username='test_student2',
            email='student2@test.edu',
            password='Password123!',
            role=User.ROLE_STUDENT,
            university_id='STU002'
        )

        # Create facility manager user
        self.manager = User.objects.create_user(
            username='test_manager',
            email='manager@test.edu',
            password='Password123!',
            role=User.ROLE_FACILITY_MANAGER,
            is_staff=True
        )

        # Create Category
        self.category_sports = FacilityCategory.objects.create(
            name="Sports Courts",
            slug="sports-courts"
        )
        self.category_gym = FacilityCategory.objects.create(
            name="Gym",
            slug="gym"
        )

        # Create Exclusive Facility (e.g. Badminton Court)
        self.court = Facility.objects.create(
            name="Badminton Court 1",
            slug="badminton-court-1",
            category=self.category_sports,
            building="Sports Center",
            floor="Ground",
            capacity=4,
            is_exclusive=True,
            booking_price=0.00,
            approval_requirement=False,
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(22, 0),
            slot_duration=60,
            assigned_manager=self.manager
        )

        # Create Shared Facility (e.g. Gym)
        self.gym = Facility.objects.create(
            name="Campus Gym",
            slug="campus-gym",
            category=self.category_gym,
            building="Sports Center",
            floor="1st Floor",
            capacity=2, # Small capacity for easy testing
            is_exclusive=False,
            booking_price=0.00,
            approval_requirement=False,
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(22, 0),
            slot_duration=60,
            assigned_manager=self.manager
        )

    def test_successful_booking_creation(self):
        target_date = timezone.localdate() + datetime.timedelta(days=2)
        booking = create_booking(
            user=self.student,
            facility_id=self.court.id,
            booking_date=target_date,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            participant_count=2,
            purpose="Friendly doubles practice"
        )

        self.assertIsNotNone(booking.id)
        self.assertTrue(booking.booking_reference.startswith("UB-"))
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertTrue(bool(booking.qr_code))
        self.assertEqual(booking.user, self.student)

    def test_double_booking_prevention_exclusive_facility(self):
        target_date = timezone.localdate() + datetime.timedelta(days=3)

        # First booking succeeds
        create_booking(
            user=self.student,
            facility_id=self.court.id,
            booking_date=target_date,
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            participant_count=2,
            purpose="First reservation"
        )

        # Second booking overlapping exact same slot must be rejected
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.student2,
                facility_id=self.court.id,
                booking_date=target_date,
                start_time=datetime.time(14, 0),
                end_time=datetime.time(15, 0),
                participant_count=2,
                purpose="Conflicting reservation"
            )

    def test_shared_facility_capacity_limit(self):
        target_date = timezone.localdate() + datetime.timedelta(days=4)

        # Gym has capacity = 2
        # Student 1 books 1 slot
        create_booking(
            user=self.student,
            facility_id=self.gym.id,
            booking_date=target_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            participant_count=1,
            purpose="Student 1 workout"
        )

        # Student 2 books 1 slot (Total = 2, reaches capacity)
        create_booking(
            user=self.student2,
            facility_id=self.gym.id,
            booking_date=target_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            participant_count=1,
            purpose="Student 2 workout"
        )

        # Third user attempting to book same slot exceeds capacity
        third_student = User.objects.create_user(username='stu3', email='stu3@test.edu', password='Password123!')
        with self.assertRaises(ValidationError):
            create_booking(
                user=third_student,
                facility_id=self.gym.id,
                booking_date=target_date,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
                participant_count=1,
                purpose="Exceeding workout"
            )

    def test_operating_hours_validation(self):
        target_date = timezone.localdate() + datetime.timedelta(days=2)
        # Court opens at 08:00, booking at 06:00 must fail
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.student,
                facility_id=self.court.id,
                booking_date=target_date,
                start_time=datetime.time(6, 0),
                end_time=datetime.time(7, 0),
                participant_count=1
            )

    def test_holiday_blocking(self):
        holiday_date = timezone.localdate() + datetime.timedelta(days=5)
        Holiday.objects.create(name="University Sports Day Holiday", date=holiday_date)

        with self.assertRaises(ValidationError):
            create_booking(
                user=self.student,
                facility_id=self.court.id,
                booking_date=holiday_date,
                start_time=datetime.time(10, 0),
                end_time=datetime.time(11, 0),
                participant_count=1
            )

    def test_cancellation_workflow(self):
        target_date = timezone.localdate() + datetime.timedelta(days=2)
        booking = create_booking(
            user=self.student,
            facility_id=self.court.id,
            booking_date=target_date,
            start_time=datetime.time(11, 0),
            end_time=datetime.time(12, 0),
            participant_count=2
        )

        cancelled = cancel_booking(booking, self.student, reason="Exam scheduled")
        self.assertEqual(cancelled.status, Booking.STATUS_CANCELLED)

    def test_qr_checkin_validation_and_replay_prevention(self):
        # QR checkin is valid on today's date
        today = timezone.localdate()
        booking = create_booking(
            user=self.student,
            facility_id=self.court.id,
            booking_date=today,
            start_time=datetime.time(16, 0),
            end_time=datetime.time(17, 0),
            participant_count=2
        )

        # 1. Successful first check-in
        res = validate_and_checkin(str(booking.token), self.manager)
        self.assertTrue(res['success'])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CHECKED_IN)
        self.assertIsNotNone(booking.checked_in_at)

        # 2. Replay check-in attempt must fail
        replay_res = validate_and_checkin(str(booking.token), self.manager)
        self.assertFalse(replay_res['success'])
        self.assertIn("ALREADY checked in", replay_res['message'])


class UniBookAPITests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='api_student',
            email='api_student@test.edu',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.category = FacilityCategory.objects.create(name="Study Pods", slug="study-pods")
        self.facility = Facility.objects.create(
            name="Library Pod 1",
            slug="library-pod-1",
            category=self.category,
            building="Library",
            floor="2nd",
            capacity=4,
            is_exclusive=True,
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(22, 0)
        )

    def test_facility_list_api(self):
        response = self.client.get('/api/facilities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_facility_availability_api(self):
        tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f'/api/facilities/{self.facility.id}/availability/?date={tomorrow}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('slots', response.data)
        self.assertTrue(len(response.data['slots']) > 0)

    def test_authenticated_booking_creation_api(self):
        self.client.force_authenticate(user=self.student)
        target_date = (timezone.localdate() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        payload = {
            'facility_id': self.facility.id,
            'booking_date': target_date,
            'start_time': '10:00',
            'end_time': '11:00',
            'participant_count': 1,
            'purpose': 'Thesis research writing'
        }
        response = self.client.post('/bookings/api/bookings/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_reference', response.data)
