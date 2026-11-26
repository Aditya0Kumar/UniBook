import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.bookings.models import Booking
from .models import Facility, FacilityCategory

User = get_user_model()


class CalendarEventsPrivacyTests(TestCase):
    """The facility calendar shows people only their own bookings, plus what is actually taken."""

    def setUp(self):
        self.student = User.objects.create_user('cal_student', 'cal_student@test.edu', 'Password123!', role=User.ROLE_STUDENT)
        self.other = User.objects.create_user('cal_other', 'cal_other@test.edu', 'Password123!', role=User.ROLE_STUDENT)
        self.faculty = User.objects.create_user('cal_faculty', 'cal_faculty@test.edu', 'Password123!', role=User.ROLE_FACULTY)
        self.manager = User.objects.create_user('cal_manager', 'cal_manager@test.edu', 'Password123!', role=User.ROLE_FACILITY_MANAGER)
        category = FacilityCategory.objects.create(name='Cal Category', slug='cal-category')
        common = dict(category=category, building='B', floor='1', booking_price=0,
                      opening_time=datetime.time(8, 0), closing_time=datetime.time(20, 0),
                      assigned_manager=self.manager)
        self.lab = Facility.objects.create(name='Shared Lab', slug='shared-lab', capacity=3, is_exclusive=False, **common)
        self.court = Facility.objects.create(name='Court', slug='court', capacity=4, is_exclusive=True, **common)
        self.day = timezone.localdate() + datetime.timedelta(days=2)

    def _book(self, user, facility, start, end, count=1, purpose='practice'):
        return Booking.objects.create(
            user=user, facility=facility, booking_date=self.day,
            start_time=datetime.time(start), end_time=datetime.time(end),
            participant_count=count, purpose=purpose, status=Booking.STATUS_CONFIRMED,
        )

    def _titles(self, facility, user=None):
        if user:
            self.client.force_login(user)
        else:
            self.client.logout()
        response = self.client.get(f'/api/facilities/{facility.pk}/calendar-events/')
        self.assertEqual(response.status_code, 200)
        return [e['title'] for e in response.json()]

    def test_shared_facility_hides_other_peoples_bookings(self):
        self._book(self.student, self.lab, 10, 12)
        self.assertEqual(self._titles(self.lab, self.student), ['My booking: practice'])
        for viewer in (self.faculty, self.manager, None):
            self.assertEqual(self._titles(self.lab, viewer), [])

    def test_shared_facility_shows_fully_booked_block(self):
        self._book(self.student, self.lab, 10, 12, count=2)
        self._book(self.other, self.lab, 11, 13, count=1)
        response_titles = self._titles(self.lab, self.faculty)
        self.assertEqual(response_titles, ['Fully Booked'])
        event = self.client.get(f'/api/facilities/{self.lab.pk}/calendar-events/').json()[0]
        self.assertTrue(event['start'].endswith('T11:00:00'))
        self.assertTrue(event['end'].endswith('T12:00:00'))

    def test_exclusive_facility_shows_booked_without_details(self):
        self._book(self.student, self.court, 10, 11, purpose='secret plan')
        self.assertEqual(self._titles(self.court, self.faculty), ['Booked'])
        self.assertEqual(self._titles(self.court, None), ['Booked'])
        self.assertEqual(self._titles(self.court, self.manager), [f'{self.student.username} - Booked'])
