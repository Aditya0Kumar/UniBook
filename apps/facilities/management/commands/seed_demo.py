import os
import urllib.request
from pathlib import Path
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from apps.accounts.models import Department, UserProfile
from apps.facilities.models import FacilityCategory, Facility, FacilityOperatingHour, Holiday
from apps.gym.models import Trainer, GymSession, GymMembership, GymReservation
from apps.mess.models import Meal, MealMenu, DietaryPreference, MealReservation
from apps.sports.models import Sport, SportsCourt, SportsEquipment, SportsReservation
from apps.laboratories.models import Laboratory, LabEquipment, LabReservationDetail
from apps.events.models import EventAuditoriumDetail, EventBookingDetail
from apps.bookings.services import create_booking
from apps.bookings.models import Booking, BookingCancellation, BookingApproval
from apps.notifications.models import Announcement, Notification
from apps.reviews.models import Review, Complaint
from apps.maintenance.models import FacilityMaintenance
from apps.payments.models import Payment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds complete realistic demo facilities, users, menus, bookings, reviews, complaints, and analytics.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Populating comprehensive UniBook campus data..."))

        # -------------------------------------------------------------
        # 1. Academic Departments
        # -------------------------------------------------------------
        dept_data = [
            ("Computer Science & Engineering", "CSE", "Department of Computer Science & Software Systems"),
            ("Electrical & Electronics", "EEE", "Department of Electrical and Embedded Systems"),
            ("Mechanical & Aerospace", "MAE", "Department of Mechanical Engineering"),
            ("School of Management", "SOM", "Faculty of Business and Management Studies"),
            ("Physical Sciences", "PHY", "School of Physics and Material Sciences"),
            ("Campus Athletics & Recreation", "ATH", "Department of Physical Education & Sports"),
        ]
        depts = {}
        for name, code, desc in dept_data:
            dept, _ = Department.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
            depts[code] = dept
        self.stdout.write(self.style.SUCCESS("✓ 6 Departments configured."))

        # -------------------------------------------------------------
        # 2. Users (Super Admin, Facility Managers, Faculty, Students)
        # -------------------------------------------------------------
        # Super Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@unibook.campus.edu',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'university_id': 'ADMIN-001',
            }
        )
        admin_user.set_password('AdminPass123!')
        admin_user.save()

        # Facility Managers
        manager_user, _ = User.objects.get_or_create(
            username='manager_demo',
            defaults={
                'email': 'manager@unibook.campus.edu',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'role': User.ROLE_FACILITY_MANAGER,
                'is_staff': True,
                'university_id': 'STAFF-104',
                'department': depts['ATH'],
                'phone_number': '+91 98230 11223'
            }
        )
        manager_user.set_password('ManagerPass123!')
        manager_user.save()

        manager_sports, _ = User.objects.get_or_create(
            username='manager_sports',
            defaults={
                'email': 'sports.lead@unibook.campus.edu',
                'first_name': 'Sunil',
                'last_name': 'Gavaskar',
                'role': User.ROLE_FACILITY_MANAGER,
                'is_staff': True,
                'university_id': 'STAFF-205',
                'department': depts['ATH'],
                'phone_number': '+91 98230 44556'
            }
        )
        manager_sports.set_password('ManagerPass123!')
        manager_sports.save()

        # Faculty Members
        faculty_user, _ = User.objects.get_or_create(
            username='faculty_demo',
            defaults={
                'email': 'faculty@unibook.campus.edu',
                'first_name': 'Dr. Aris',
                'last_name': 'Venkatesh',
                'role': User.ROLE_FACULTY,
                'university_id': 'FAC-209',
                'department': depts['CSE'],
                'phone_number': '+91 97120 44556'
            }
        )
        faculty_user.set_password('FacultyPass123!')
        faculty_user.save()

        faculty_sharma, _ = User.objects.get_or_create(
            username='faculty_sharma',
            defaults={
                'email': 'n.sharma@unibook.campus.edu',
                'first_name': 'Dr. Neha',
                'last_name': 'Sharma',
                'role': User.ROLE_FACULTY,
                'university_id': 'FAC-312',
                'department': depts['PHY'],
                'phone_number': '+91 97120 99887'
            }
        )
        faculty_sharma.set_password('FacultyPass123!')
        faculty_sharma.save()

        # Students
        student_user, _ = User.objects.get_or_create(
            username='student_demo',
            defaults={
                'email': 'student@unibook.campus.edu',
                'first_name': 'Pooja',
                'last_name': 'Iyer',
                'role': User.ROLE_STUDENT,
                'university_id': 'STU-2026-441',
                'department': depts['CSE'],
                'phone_number': '+91 95450 77889'
            }
        )
        student_user.set_password('StudentPass123!')
        student_user.save()

        student_rahul, _ = User.objects.get_or_create(
            username='student_rahul',
            defaults={
                'email': 'rahul.verma@unibook.campus.edu',
                'first_name': 'Rahul',
                'last_name': 'Verma',
                'role': User.ROLE_STUDENT,
                'university_id': 'STU-2026-512',
                'department': depts['MAE'],
                'phone_number': '+91 95450 11223'
            }
        )
        student_rahul.set_password('StudentPass123!')
        student_rahul.save()

        student_ananya, _ = User.objects.get_or_create(
            username='student_ananya',
            defaults={
                'email': 'ananya.singh@unibook.campus.edu',
                'first_name': 'Ananya',
                'last_name': 'Singh',
                'role': User.ROLE_STUDENT,
                'university_id': 'STU-2026-620',
                'department': depts['SOM'],
                'phone_number': '+91 95450 33445'
            }
        )
        student_ananya.set_password('StudentPass123!')
        student_ananya.save()

        self.stdout.write(self.style.SUCCESS("✓ Active users seeded across all 4 roles."))

        # -------------------------------------------------------------
        # 3. 13 Facility Categories
        # -------------------------------------------------------------
        categories_data = [
            ("Gym", "gym", "dumbbell", "Campus fitness centers, weight rooms, cardio zones, and fitness studios."),
            ("Mess and Dining", "mess-and-dining", "utensils", "University cafeterias, dining halls, and student messes."),
            ("Sports", "sports", "trophy", "Indoor and outdoor courts for badminton, basketball, tennis, and football."),
            ("Swimming Pool", "swimming-pool", "waves", "Olympic-size swimming pools and diving lanes."),
            ("Auditorium", "auditorium", "theater", "High-capacity halls for symposiums, cultural events, and convocations."),
            ("Seminar Hall", "seminar-hall", "presentation", "Audio-visual equipped halls for guest lectures and presentations."),
            ("Computer Laboratory", "computer-laboratory", "laptop", "High-performance computing and software engineering labs."),
            ("Research Laboratory", "research-laboratory", "microscope", "Specialized research spaces for graduate and faculty projects."),
            ("Library", "library", "book-open", "Quiet study halls, group discussion pods, and digital archives."),
            ("Conference Room", "conference-room", "users", "Executive meeting rooms with hybrid video conferencing."),
            ("Music Room", "music-room", "music", "Acoustically treated rooms with instruments and recording audio."),
            ("Medical and Wellness", "medical-and-wellness", "heart-pulse", "Health center, counseling rooms, and physiotherapy cabins."),
            ("Recreation Room", "recreation-room", "gamepad-2", "Student lounge with table tennis, chess, and foosball."),
        ]
        cats = {}
        for name, slug, icon, desc in categories_data:
            cat, _ = FacilityCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'description': desc})
            cats[slug] = cat

        # -------------------------------------------------------------
        # 4. Mandatory Facilities
        # -------------------------------------------------------------
        facilities_spec = [
            {
                'name': 'Campus Central Gymnasium & Strength Lab',
                'slug': 'campus-central-gymnasium',
                'category': cats['gym'],
                'description': 'Fully air-conditioned fitness center featuring Olympic barbells, power racks, cardio rowers, and personal trainer supervision.',
                'building': 'Student Sports Complex',
                'floor': '1st Floor',
                'capacity': 40,
                'is_exclusive': False,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'North Dining Hall & Student Mess',
                'slug': 'north-dining-hall-mess',
                'category': cats['mess-and-dining'],
                'description': 'Main residential dining hall serving fresh breakfast, thali lunches, evening snacks, and hygienic buffet dinners.',
                'building': 'North Hostel Cluster A',
                'floor': 'Ground Floor',
                'capacity': 150,
                'is_exclusive': False,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(7, 30),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'South Annex Dining Complex',
                'slug': 'south-annex-dining-complex',
                'category': cats['mess-and-dining'],
                'description': 'South campus dining pavilion featuring healthy meal subscriptions, live south Indian counter, and salad bar.',
                'building': 'Hostel Block 4',
                'floor': 'Ground Floor',
                'capacity': 120,
                'is_exclusive': False,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(7, 30),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'Badminton Court 1 (Indoor Wooden Teakwood)',
                'slug': 'badminton-court-1',
                'category': cats['sports'],
                'description': 'BWF-certified indoor court with anti-glare LED illumination, shock-absorbing teakwood flooring, and net setup.',
                'building': 'Indoor Stadium',
                'floor': 'Ground Floor',
                'capacity': 4,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Badminton Court 2 (Synthetic Mat Court)',
                'slug': 'badminton-court-2',
                'category': cats['sports'],
                'description': 'Professional vinyl synthetic mat court suitable for competitive practice and student tournaments.',
                'building': 'Indoor Stadium',
                'floor': 'Ground Floor',
                'capacity': 4,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Badminton Court 3 (Recreational Glass-Back Court)',
                'slug': 'badminton-court-3',
                'category': cats['sports'],
                'description': 'Recreational court equipped with spectator seating gallery and electronic scoreboard.',
                'building': 'Indoor Stadium',
                'floor': 'Ground Floor',
                'capacity': 4,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Basketball Court A (Arena Hardwood Court)',
                'slug': 'basketball-court-a-arena',
                'category': cats['sports'],
                'description': 'Official FIBA dimension court with hydraulic glass backboards, perimeter padding, and electronic shot clocks.',
                'building': 'Indoor Stadium',
                'floor': 'Main Arena',
                'capacity': 10,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Basketball Court B (Outdoor Floodlit Court)',
                'slug': 'basketball-court-b-outdoor',
                'category': cats['sports'],
                'description': 'Outdoor acrylic court equipped with high-intensity floodlights for evening student matches.',
                'building': 'Sports Grounds',
                'floor': 'Outdoor Complex',
                'capacity': 10,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(21, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Main Campus Turf Football Stadium',
                'slug': 'main-campus-football-stadium',
                'category': cats['sports'],
                'description': 'Full-size FIFA regulation artificial turf pitch with running track perimeter and team dugouts.',
                'building': 'Athletics Ground',
                'floor': 'Open Grounds',
                'capacity': 22,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(21, 0),
                'slot_mins': 90,
                'manager': manager_sports
            },
            {
                'name': 'Olympic Aquatics Complex & Swimming Pool',
                'slug': 'olympic-aquatics-complex',
                'category': cats['swimming-pool'],
                'description': '50-meter 8-lane temperature-controlled swimming pool with dedicated lifeguard on duty and lane lines.',
                'building': 'Aquatics Center',
                'floor': 'Ground Floor',
                'capacity': 25,
                'is_exclusive': False,
                'price': 50.00,
                'approval': False,
                'open': datetime.time(6, 0),
                'close': datetime.time(21, 0),
                'slot_mins': 60,
                'manager': manager_sports
            },
            {
                'name': 'Advanced AI & Cloud Computing Lab',
                'slug': 'advanced-ai-cloud-lab',
                'category': cats['computer-laboratory'],
                'description': 'Equipped with 60 high-end Linux workstations connected to high-performance GPU compute clusters for deep learning.',
                'building': 'Turing Computer Complex',
                'floor': '3rd Floor',
                'capacity': 60,
                'is_exclusive': False,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(8, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 120,
                'manager': manager_user
            },
            {
                'name': 'Robotics & Cyber-Physical Systems Lab',
                'slug': 'robotics-cps-lab',
                'category': cats['research-laboratory'],
                'description': 'Testbeds for autonomous mobile robots, robotic arms, embedded microcontroller stations, and sensor benches.',
                'building': 'Engineering Tower',
                'floor': '2nd Floor',
                'capacity': 30,
                'is_exclusive': True,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(8, 0),
                'close': datetime.time(20, 0),
                'slot_mins': 120,
                'manager': manager_user
            },
            {
                'name': 'Nanotechnology & Materials Research Lab',
                'slug': 'nanotech-materials-lab',
                'category': cats['research-laboratory'],
                'description': 'Cleanroom environment for chemical synthesis, optical microscopy, and material characterization.',
                'building': 'Science Complex',
                'floor': '1st Floor',
                'capacity': 20,
                'is_exclusive': True,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(8, 0),
                'close': datetime.time(20, 0),
                'slot_mins': 120,
                'manager': manager_user
            },
            {
                'name': 'Dr. A.P.J. Abdul Kalam Memorial Auditorium',
                'slug': 'kalam-memorial-auditorium',
                'category': cats['auditorium'],
                'description': 'Grand 800-seat auditorium equipped with motorized proscenium curtains, line-array acoustics, and dual 4K laser projection.',
                'building': 'Central Administrative Block',
                'floor': 'Main Level',
                'capacity': 800,
                'is_exclusive': True,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(8, 0),
                'close': datetime.time(22, 0),
                'slot_mins': 180,
                'manager': manager_user
            },
            {
                'name': 'Sir C.V. Raman Science Auditorium',
                'slug': 'raman-science-auditorium',
                'category': cats['auditorium'],
                'description': 'Stepped lecture auditorium with 300 seating capacity, live broadcast streaming deck, and wireless conference microphones.',
                'building': 'Science Quadrangle',
                'floor': 'Ground Floor',
                'capacity': 300,
                'is_exclusive': True,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(8, 0),
                'close': datetime.time(21, 0),
                'slot_mins': 120,
                'manager': manager_user
            },
            {
                'name': 'Seminar Hall 101 - Tech Tower',
                'slug': 'seminar-hall-101',
                'category': cats['seminar-hall'],
                'description': '120-seat interactive seminar room with dual smart podiums, digital whiteboard, and surround sound.',
                'building': 'Tech Tower',
                'floor': '1st Floor',
                'capacity': 120,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(8, 0),
                'close': datetime.time(20, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'Seminar Hall 202 - Management Wing',
                'slug': 'seminar-hall-202',
                'category': cats['seminar-hall'],
                'description': 'Harvard-style amphitheater seminar hall ideal for case studies, business presentations, and guest speakers.',
                'building': 'School of Management',
                'floor': '2nd Floor',
                'capacity': 90,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(8, 0),
                'close': datetime.time(20, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': "Dean's Executive Seminar Room",
                'slug': 'deans-executive-seminar-room',
                'category': cats['seminar-hall'],
                'description': 'Executive round-table setup with integrated personal display monitors and teleconference capabilities.',
                'building': 'Main Senate Building',
                'floor': '3rd Floor',
                'capacity': 40,
                'is_exclusive': True,
                'price': 0.00,
                'approval': True,
                'open': datetime.time(9, 0),
                'close': datetime.time(19, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'Library Silent Discussion Pod A',
                'slug': 'library-discussion-pod-a',
                'category': cats['library'],
                'description': 'Acoustic glass enclosed study room equipped with high-speed wired Ethernet and presentation screen for research groups.',
                'building': 'Central Library',
                'floor': '2nd Floor',
                'capacity': 8,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(8, 0),
                'close': datetime.time(23, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
            {
                'name': 'Digital Media & Research Pod B',
                'slug': 'digital-media-research-pod-b',
                'category': cats['library'],
                'description': 'Equipped with dual monitors, audio monitors, and digital library catalog search terminals.',
                'building': 'Central Library',
                'floor': '2nd Floor',
                'capacity': 6,
                'is_exclusive': True,
                'price': 0.00,
                'approval': False,
                'open': datetime.time(8, 0),
                'close': datetime.time(23, 0),
                'slot_mins': 60,
                'manager': manager_user
            },
        ]

        created_facilities = {}
        for f_data in facilities_spec:
            facility, _ = Facility.objects.get_or_create(
                slug=f_data['slug'],
                defaults={
                    'name': f_data['name'],
                    'category': f_data['category'],
                    'description': f_data['description'],
                    'building': f_data['building'],
                    'floor': f_data['floor'],
                    'campus': 'Main Campus',
                    'capacity': f_data['capacity'],
                    'is_exclusive': f_data['is_exclusive'],
                    'booking_price': f_data['price'],
                    'approval_requirement': f_data['approval'],
                    'opening_time': f_data['open'],
                    'closing_time': f_data['close'],
                    'slot_duration': f_data['slot_mins'],
                    'assigned_manager': f_data['manager'],
                    'facility_status': Facility.STATUS_ACTIVE
                }
            )
            created_facilities[f_data['slug']] = facility

            for day in range(7):
                FacilityOperatingHour.objects.get_or_create(
                    facility=facility,
                    day_of_week=day,
                    defaults={'opening_time': f_data['open'], 'closing_time': f_data['close'], 'is_closed': False}
                )

        # Ensure media directory and attach facility images
        media_fac_dir = Path(settings.MEDIA_ROOT) / 'facilities'
        media_fac_dir.mkdir(parents=True, exist_ok=True)

        FACILITY_ONLINE_URLS = {
            'campus-central-gymnasium': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1000&q=80',
            'north-dining-hall-mess': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1000&q=80',
            'south-annex-dining-complex': 'https://images.unsplash.com/photo-1567521464027-f127ff144326?auto=format&fit=crop&w=1000&q=80',
            'badminton-court-1': 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=1000&q=80',
            'badminton-court-2': 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=1000&q=80',
            'badminton-court-3': 'https://images.unsplash.com/photo-1599474924187-334a4ae5bd3c?auto=format&fit=crop&w=1000&q=80',
            'basketball-court-a-arena': 'https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=1000&q=80',
            'basketball-court-b-outdoor': 'https://images.unsplash.com/photo-1519861531473-9200262188bf?auto=format&fit=crop&w=1000&q=80',
            'main-campus-football-stadium': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=1000&q=80',
            'olympic-aquatics-complex': 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1000&q=80',
            'advanced-ai-cloud-lab': 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1000&q=80',
            'robotics-cps-lab': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1000&q=80',
            'nanotech-materials-lab': 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=1000&q=80',
            'kalam-memorial-auditorium': 'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&w=1000&q=80',
            'raman-science-auditorium': 'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1000&q=80',
            'seminar-hall-101': 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80',
            'seminar-hall-202': 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1000&q=80',
            'deans-executive-seminar-room': 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&w=1000&q=80',
            'library-discussion-pod-a': 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1000&q=80',
            'digital-media-research-pod-b': 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=1000&q=80',
        }

        for slug, fac in created_facilities.items():
            img_rel = f"facilities/{slug}.jpg"
            img_file = media_fac_dir / f"{slug}.jpg"
            if not img_file.exists() and slug in FACILITY_ONLINE_URLS:
                try:
                    req = urllib.request.Request(FACILITY_ONLINE_URLS[slug], headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as resp, open(img_file, 'wb') as out_f:
                        out_f.write(resp.read())
                except Exception:
                    pass
            if img_file.exists():
                fac.image = img_rel
                fac.save(update_fields=['image'])

        self.stdout.write(self.style.SUCCESS("✓ 18 Mandated facilities configured with high-res media imagery."))

        # -------------------------------------------------------------
        # 5. Gym Sessions, Trainers & Memberships
        # -------------------------------------------------------------
        trainer1, _ = Trainer.objects.get_or_create(
            name='Coach Vikram Rao',
            defaults={
                'specialization': 'Strength & Conditioning',
                'bio': 'CSCS Certified coach with 8+ years preparing university lifters and collegiate athletes.',
                'is_available': True
            }
        )
        trainer2, _ = Trainer.objects.get_or_create(
            name='Coach Sarah Jenkins',
            defaults={
                'specialization': 'HIIT & Functional Mobility',
                'bio': 'Functional movement trainer specialized in core conditioning and cardiovascular endurance.',
                'is_available': True
            }
        )

        gym_fac = created_facilities.get('campus-central-gymnasium')
        if gym_fac:
            session_m, _ = GymSession.objects.get_or_create(
                facility=gym_fac,
                session_type=GymSession.SESSION_MORNING,
                defaults={
                    'title': 'Morning Conditioning & Cardio',
                    'start_time': datetime.time(6, 0),
                    'end_time': datetime.time(10, 0),
                    'capacity': 40,
                    'trainer': trainer1
                }
            )
            session_a, _ = GymSession.objects.get_or_create(
                facility=gym_fac,
                session_type=GymSession.SESSION_AFTERNOON,
                defaults={
                    'title': 'Afternoon Open Workout',
                    'start_time': datetime.time(12, 0),
                    'end_time': datetime.time(16, 0),
                    'capacity': 40,
                    'trainer': trainer2
                }
            )
            session_e, _ = GymSession.objects.get_or_create(
                facility=gym_fac,
                session_type=GymSession.SESSION_EVENING,
                defaults={
                    'title': 'Evening Powerlifting & Core',
                    'start_time': datetime.time(17, 0),
                    'end_time': datetime.time(22, 0),
                    'capacity': 40,
                    'trainer': trainer1
                }
            )

        GymMembership.objects.get_or_create(
            user=student_user,
            defaults={
                'plan': GymMembership.PLAN_SEMESTER,
                'start_date': timezone.localdate() - datetime.timedelta(days=30),
                'end_date': timezone.localdate() + datetime.timedelta(days=90),
                'is_active': True
            }
        )

        # -------------------------------------------------------------
        # 6. Mess Dining Meals & Weekly Menus
        # -------------------------------------------------------------
        meals_info = [
            (Meal.MEAL_BREAKFAST, "Campus Breakfast", datetime.time(7, 30), datetime.time(9, 30)),
            (Meal.MEAL_LUNCH, "Nutritious Lunch", datetime.time(12, 0), datetime.time(14, 30)),
            (Meal.MEAL_SNACKS, "High Tea & Snacks", datetime.time(17, 0), datetime.time(18, 30)),
            (Meal.MEAL_DINNER, "Balanced Dinner", datetime.time(19, 30), datetime.time(21, 45)),
        ]
        created_meals = {}
        for m_type, m_name, s_time, e_time in meals_info:
            meal_obj, _ = Meal.objects.get_or_create(
                meal_type=m_type,
                defaults={'name': m_name, 'start_time': s_time, 'end_time': e_time}
            )
            created_meals[m_type] = meal_obj

        mess1 = created_facilities.get('north-dining-hall-mess')
        if mess1:
            menu_samples = [
                (0, Meal.MEAL_BREAKFAST, "Idli, Sambar, Medu Vada, Coconut Chutney, Masala Omelette, Tea/Coffee"),
                (0, Meal.MEAL_LUNCH, "Paneer Butter Masala, Dal Tadka, Jeera Rice, Tandoori Roti, Boondi Raita, Gulab Jamun"),
                (0, Meal.MEAL_DINNER, "Kadai Veggies, Yellow Dal, Phulka, Steamed Basmati Rice, Fruit Salad"),
                (1, Meal.MEAL_BREAKFAST, "Aloo Paratha, Curd, Poha, Boiled Eggs, Fresh Juice, Chai"),
                (1, Meal.MEAL_LUNCH, "Rajma Masala, Kashmiri Pulao, Curd, Mix Veg, Chapatis, Kheer"),
                (1, Meal.MEAL_DINNER, "Egg Curry / Malai Kofta, Dal Makhani, Paratha, Rice, Cucumber Salad"),
                (2, Meal.MEAL_BREAKFAST, "Uttapam, Upma, Chana Gravy, Sambar, Toast & Butter, Coffee"),
                (2, Meal.MEAL_LUNCH, "Chole Bhature, Steamed Rice, Dal Palak, Onion Salad, Ice Cream"),
                (2, Meal.MEAL_DINNER, "Matar Paneer, Dal Fry, Roti, Veg Biryani, Mint Raita"),
                (3, Meal.MEAL_BREAKFAST, "Masala Dosa, Sambar, Tomato Chutney, Boiled Eggs, Masala Chai"),
                (3, Meal.MEAL_LUNCH, "Veg Pulao, Dal Makhani, Mixed Vegetable Korma, Phulka, Rasam, Gulab Jamun"),
                (3, Meal.MEAL_DINNER, "Dum Aloo, Dal Tadka, Roti, Steamed Basmati Rice, Green Salad"),
                (4, Meal.MEAL_BREAKFAST, "Methi Thepla, Curd, Pickle, Boiled Eggs, Banana, Filter Coffee"),
                (4, Meal.MEAL_LUNCH, "Hyderabadi Veg Biryani, Mirchi Ka Salan, Onion Raitha, Paneer Tikka Masala"),
                (4, Meal.MEAL_DINNER, "Aloo Gobi, Dal Fry, Chapati, Jeera Rice, Custard"),
                (5, Meal.MEAL_BREAKFAST, "Puri Bhaji, Kesari Bath, Boiled Eggs, Orange Juice, Tea"),
                (5, Meal.MEAL_LUNCH, "South Indian Thali: Sambar, Rasam, Poriyal, Curd Rice, Appalam, Payasam"),
                (5, Meal.MEAL_DINNER, "Veg Manchurian, Hakka Noodles, Fried Rice, Sweet Corn Soup"),
                (6, Meal.MEAL_BREAKFAST, "Chole Bhature, Fresh Lassi, Bread Butter Jam, Coffee"),
                (6, Meal.MEAL_LUNCH, "Special Sunday Feast: Paneer Lababdar, Dal Bukhara, Butter Naan, Pulao, Jalebi"),
                (6, Meal.MEAL_DINNER, "Light Khichdi, Gujarati Kadhi, Roasted Papad, Seasonal Fruits"),
            ]
            for day, m_type, dishes in menu_samples:
                MealMenu.objects.get_or_create(
                    facility=mess1,
                    day_of_week=day,
                    meal=created_meals[m_type],
                    defaults={'dishes': dishes, 'special_dietary_options': 'Jain and Vegan counters available'}
                )

        DietaryPreference.objects.get_or_create(
            user=student_user,
            defaults={'preference': DietaryPreference.PREF_VEG, 'allergies': 'None'}
        )
        DietaryPreference.objects.get_or_create(
            user=student_ananya,
            defaults={'preference': DietaryPreference.PREF_VEGAN, 'allergies': 'Lactose Intolerant'}
        )

        # -------------------------------------------------------------
        # 7. Sports Equipment & Details
        # -------------------------------------------------------------
        badminton_sport, _ = Sport.objects.get_or_create(
            name='Badminton',
            defaults={'icon': 'trophy', 'is_team_sport': False, 'players_per_side': 2}
        )
        basketball_sport, _ = Sport.objects.get_or_create(
            name='Basketball',
            defaults={'icon': 'trophy', 'is_team_sport': True, 'players_per_side': 5}
        )
        football_sport, _ = Sport.objects.get_or_create(
            name='Football',
            defaults={'icon': 'trophy', 'is_team_sport': True, 'players_per_side': 11}
        )

        SportsEquipment.objects.get_or_create(
            sport=badminton_sport,
            name='Yonex Carbonex Racket Set',
            defaults={'total_quantity': 20, 'available_quantity': 16, 'rental_fee': 20.00}
        )
        SportsEquipment.objects.get_or_create(
            sport=basketball_sport,
            name='Spalding Composite Leather Basketball',
            defaults={'total_quantity': 15, 'available_quantity': 12, 'rental_fee': 0.00}
        )
        SportsEquipment.objects.get_or_create(
            sport=football_sport,
            name='FIFA Quality Pro Football Ball',
            defaults={'total_quantity': 12, 'available_quantity': 10, 'rental_fee': 0.00}
        )

        # -------------------------------------------------------------
        # 8. Laboratory Equipment
        # -------------------------------------------------------------
        ai_lab = created_facilities.get('advanced-ai-cloud-lab')
        if ai_lab:
            lab_prof, _ = Laboratory.objects.get_or_create(
                facility=ai_lab,
                defaults={'lab_type': Laboratory.LAB_COMPUTER, 'safety_guidelines': 'Strict access card entry.'}
            )
            LabEquipment.objects.get_or_create(
                laboratory=lab_prof,
                name='NVIDIA DGX A100 8-GPU Compute Station',
                defaults={'total_count': 4, 'available_count': 4}
            )
            LabEquipment.objects.get_or_create(
                laboratory=lab_prof,
                name='High-Density NVMe 100TB Storage Array',
                defaults={'total_count': 2, 'available_count': 2}
            )

        # -------------------------------------------------------------
        # 9. Campus Announcements
        # -------------------------------------------------------------
        Announcement.objects.get_or_create(
            title='Annual Inter-Department Badminton Tournament 2026',
            defaults={
                'content': 'Registrations are now open for all student and faculty doubles pairings. Tournament takes place at Indoor Stadium Courts 1-3 this weekend.',
                'category': Announcement.CATEGORY_SPORTS,
                'target_role': Announcement.TARGET_ALL,
                'author': admin_user
            }
        )
        Announcement.objects.get_or_create(
            title='Scheduled AC Maintenance in Turing Tech Tower',
            defaults={
                'content': 'Routine HVAC maintenance scheduled for Thursday evening from 20:00 to 22:00. Computer laboratories will operate on auxiliary cooling.',
                'category': Announcement.CATEGORY_MAINTENANCE,
                'target_role': Announcement.TARGET_ALL,
                'author': admin_user
            }
        )
        Announcement.objects.get_or_create(
            title='New Olympic Aquatics Lane Booking Rules',
            defaults={
                'content': 'Morning lap swimming hours from 06:00 to 09:00 are reserved for student & faculty fitness pass holders. Proper swimwear required.',
                'category': Announcement.CATEGORY_POLICY,
                'target_role': Announcement.TARGET_ALL,
                'author': admin_user
            }
        )

        # -------------------------------------------------------------
        # 10. Verified Reviews
        # -------------------------------------------------------------
        review_data = [
            (created_facilities['badminton-court-1'], student_user, 5, 'Superb teakwood floor! Lighting is bright and glare-free. Easy to book via UniBook.'),
            (created_facilities['campus-central-gymnasium'], faculty_user, 5, 'Clean locker rooms, modern equipment, and attentive trainers. Highly recommended.'),
            (created_facilities['north-dining-hall-mess'], student_rahul, 4, 'Lunch thali is very balanced and tasty. The contactless QR entry saves a lot of queue time.'),
            (created_facilities['advanced-ai-cloud-lab'], student_ananya, 5, 'Blazing fast GPU compute nodes. Saved our deep learning capstone team weeks of training time!'),
            (created_facilities['olympic-aquatics-complex'], faculty_sharma, 5, 'Crystal clear temperature-controlled water. Excellent morning workout experience.'),
            (created_facilities['seminar-hall-101'], faculty_user, 4, 'Audio system and motorized projection worked flawlessly during our symposium.'),
        ]
        for fac, usr, rating, comment in review_data:
            Review.objects.update_or_create(
                facility=fac,
                user=usr,
                defaults={'rating': rating, 'comment': comment, 'is_approved': True}
            )

        # -------------------------------------------------------------
        # 11. Complaints & Maintenance Issues
        # -------------------------------------------------------------
        Complaint.objects.get_or_create(
            facility=created_facilities['badminton-court-2'],
            user=student_rahul,
            title='Net tension cable loose on Court 2',
            defaults={
                'description': 'The center net height has dropped by ~2 inches due to loose ratchet cable. Needs tightening before tournament.',
                'status': Complaint.STATUS_IN_REVIEW,
                'admin_remarks': 'Facility manager Sunil Gavaskar assigned for ratchet replacement on Wednesday.'
            }
        )
        Complaint.objects.get_or_create(
            facility=created_facilities['advanced-ai-cloud-lab'],
            user=student_user,
            title='Air conditioner temperature too low in Row 4',
            defaults={
                'description': 'The ceiling cassette AC right above terminal stations 20-25 is running at 18C and blowing cold air directly onto monitors.',
                'status': Complaint.STATUS_RESOLVED,
                'admin_remarks': 'HVAC technician calibrated thermostat to 23C.',
                'resolved_by': admin_user
            }
        )
        Complaint.objects.get_or_create(
            facility=created_facilities['north-dining-hall-mess'],
            user=student_ananya,
            title='Vegan counter ran out of almond milk at 08:30',
            defaults={
                'description': 'During breakfast rush hour the vegan beverage counter was empty for 20 minutes.',
                'status': Complaint.STATUS_PENDING,
                'admin_remarks': ''
            }
        )

        # -------------------------------------------------------------
        # 12. Scheduled Maintenance Windows
        # -------------------------------------------------------------
        now_dt = timezone.now()
        FacilityMaintenance.objects.get_or_create(
            facility=created_facilities['main-campus-football-stadium'],
            title='Turf Pitch Aeration and Line Marking',
            defaults={
                'description': 'Routine seasonal pitch turf brushing, rubber infill leveling, and boundary line repainting.',
                'start_time': now_dt + datetime.timedelta(days=4),
                'end_time': now_dt + datetime.timedelta(days=4, hours=6),
                'status': FacilityMaintenance.STATUS_SCHEDULED,
                'created_by': admin_user
            }
        )
        FacilityMaintenance.objects.get_or_create(
            facility=created_facilities['kalam-memorial-auditorium'],
            title='Laser Projector Lamp Replacement and Acoustic Calibration',
            defaults={
                'description': 'Scheduled vendor maintenance for primary 4K Christie projector.',
                'start_time': now_dt - datetime.timedelta(days=2),
                'end_time': now_dt - datetime.timedelta(days=2, hours=4),
                'status': FacilityMaintenance.STATUS_COMPLETED,
                'created_by': admin_user
            }
        )

        # -------------------------------------------------------------
        # 13. Rich Historical & Active Bookings (Past 7 days + Today + Upcoming)
        # -------------------------------------------------------------
        today = timezone.localdate()

        # A. Past Bookings (Last 6 Days to populate Chart.js trends & analytics)
        past_reservations = [
            (today - datetime.timedelta(days=6), datetime.time(9, 0), datetime.time(10, 0), created_facilities['badminton-court-1'], student_user, 2, "Singles practice session", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=6), datetime.time(18, 0), datetime.time(19, 0), created_facilities['campus-central-gymnasium'], student_rahul, 1, "Evening push-pull workout", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=5), datetime.time(10, 0), datetime.time(11, 0), created_facilities['basketball-court-a-arena'], student_user, 10, "Hostel 3 vs Hostel 5 scrimmage", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=5), datetime.time(14, 0), datetime.time(16, 0), created_facilities['advanced-ai-cloud-lab'], faculty_user, 20, "CS401 Lab Assignment 3 testing", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=4), datetime.time(8, 0), datetime.time(9, 0), created_facilities['olympic-aquatics-complex'], student_ananya, 1, "Morning lap swim session", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=4), datetime.time(11, 0), datetime.time(12, 0), created_facilities['badminton-court-2'], student_rahul, 2, "Inter-year practice match", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=4), datetime.time(17, 0), datetime.time(18, 0), created_facilities['campus-central-gymnasium'], student_user, 1, "Powerlifting workout", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=3), datetime.time(9, 0), datetime.time(10, 0), created_facilities['library-discussion-pod-a'], student_ananya, 4, "Final year capstone discussion", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=3), datetime.time(15, 0), datetime.time(16, 0), created_facilities['seminar-hall-202'], faculty_sharma, 45, "Invited Talk: Quantum Sensors", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=2), datetime.time(10, 0), datetime.time(11, 0), created_facilities['badminton-court-3'], student_user, 2, "Recreational rally with batchmates", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=2), datetime.time(16, 0), datetime.time(17, 0), created_facilities['campus-central-gymnasium'], student_rahul, 1, "Leg day workout", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=1), datetime.time(9, 0), datetime.time(10, 0), created_facilities['badminton-court-1'], student_ananya, 2, "Morning badminton warmup", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=1), datetime.time(14, 0), datetime.time(16, 0), created_facilities['robotics-cps-lab'], faculty_user, 12, "Autonomous rover ROS testing", Booking.STATUS_COMPLETED),
            (today - datetime.timedelta(days=1), datetime.time(19, 0), datetime.time(20, 0), created_facilities['north-dining-hall-mess'], student_user, 1, "Special dinner meal pass", Booking.STATUS_COMPLETED),
        ]

        for b_date, s_time, e_time, fac, usr, part_count, purpose, status in past_reservations:
            b_obj, created = Booking.objects.get_or_create(
                user=usr,
                facility=fac,
                booking_date=b_date,
                start_time=s_time,
                end_time=e_time,
                defaults={
                    'participant_count': part_count,
                    'purpose': purpose,
                    'status': status,
                    'payment_status': Booking.PAYMENT_FREE if fac.is_free else Booking.PAYMENT_PAID,
                }
            )

        # B. Today's Bookings (Active & Checked-In for Live Scanner Demo)
        today_checked_in = [
            (datetime.time(8, 0), datetime.time(9, 0), created_facilities['badminton-court-1'], student_user, 2, "Morning pre-class practice"),
            (datetime.time(9, 0), datetime.time(10, 0), created_facilities['campus-central-gymnasium'], student_rahul, 1, "Morning HIIT with Coach Sarah"),
            (datetime.time(10, 0), datetime.time(11, 0), created_facilities['library-discussion-pod-a'], student_ananya, 4, "Research paper reading group"),
        ]
        for s_time, e_time, fac, usr, part_count, purpose in today_checked_in:
            b_obj, _ = Booking.objects.get_or_create(
                user=usr,
                facility=fac,
                booking_date=today,
                start_time=s_time,
                end_time=e_time,
                defaults={
                    'participant_count': part_count,
                    'purpose': purpose,
                    'status': Booking.STATUS_CHECKED_IN,
                    'payment_status': Booking.PAYMENT_FREE,
                    'checked_in_at': timezone.now() - datetime.timedelta(minutes=45),
                    'checked_in_by': manager_user
                }
            )

        # C. Today's Expected Bookings (Confirmed)
        today_expected = [
            (datetime.time(16, 0), datetime.time(17, 0), created_facilities['badminton-court-2'], student_rahul, 2, "Evening singles ladder challenge"),
            (datetime.time(18, 0), datetime.time(19, 0), created_facilities['basketball-court-a-arena'], student_user, 10, "University team trials"),
            (datetime.time(19, 30), datetime.time(20, 30), created_facilities['north-dining-hall-mess'], student_ananya, 1, "Vegan dinner pass reservation"),
        ]
        for s_time, e_time, fac, usr, part_count, purpose in today_expected:
            b_obj, _ = Booking.objects.get_or_create(
                user=usr,
                facility=fac,
                booking_date=today,
                start_time=s_time,
                end_time=e_time,
                defaults={
                    'participant_count': part_count,
                    'purpose': purpose,
                    'status': Booking.STATUS_CONFIRMED,
                    'payment_status': Booking.PAYMENT_FREE
                }
            )

        # D. Upcoming Bookings (Tomorrow & Day After Tomorrow)
        tomorrow = today + datetime.timedelta(days=1)
        day_after = today + datetime.timedelta(days=2)

        try:
            create_booking(
                user=student_user,
                facility_id=created_facilities['badminton-court-1'].id,
                booking_date=tomorrow,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
                participant_count=2,
                purpose="Friendly practice match with roommate"
            )
        except Exception:
            pass

        try:
            create_booking(
                user=student_rahul,
                facility_id=created_facilities['olympic-aquatics-complex'].id,
                booking_date=tomorrow,
                start_time=datetime.time(7, 0),
                end_time=datetime.time(8, 0),
                participant_count=1,
                purpose="Cardio lap training"
            )
        except Exception:
            pass

        try:
            create_booking(
                user=student_ananya,
                facility_id=created_facilities['campus-central-gymnasium'].id,
                booking_date=day_after,
                start_time=datetime.time(18, 0),
                end_time=datetime.time(19, 0),
                participant_count=1,
                purpose="Strength workout with Coach Vikram"
            )
        except Exception:
            pass

        # E. Pending Approval Requests (For Testing Manager Approvals Portal)
        pending_requests = [
            (tomorrow, datetime.time(14, 0), datetime.time(17, 0), created_facilities['kalam-memorial-auditorium'], faculty_user, 350, "Annual IEEE Student Branch Inauguration & Keynote"),
            (day_after, datetime.time(10, 0), datetime.time(12, 0), created_facilities['advanced-ai-cloud-lab'], student_user, 15, "RoboCup Simulation League Hackathon Session"),
            (day_after, datetime.time(15, 0), datetime.time(16, 0), created_facilities['deans-executive-seminar-room'], faculty_sharma, 25, "Board of Studies Curriculum Review 2026"),
        ]
        for b_date, s_time, e_time, fac, usr, part_count, purpose in pending_requests:
            b_obj, created = Booking.objects.get_or_create(
                user=usr,
                facility=fac,
                booking_date=b_date,
                start_time=s_time,
                end_time=e_time,
                defaults={
                    'participant_count': part_count,
                    'purpose': purpose,
                    'status': Booking.STATUS_PENDING,
                    'payment_status': Booking.PAYMENT_FREE
                }
            )

        # F. Cancelled Booking Example
        cancelled_b, _ = Booking.objects.get_or_create(
            user=student_rahul,
            facility=created_facilities['badminton-court-2'],
            booking_date=tomorrow,
            start_time=datetime.time(11, 0),
            end_time=datetime.time(12, 0),
            defaults={
                'participant_count': 2,
                'purpose': "Canceled due to quiz reschedule",
                'status': Booking.STATUS_CANCELLED,
                'payment_status': Booking.PAYMENT_FREE
            }
        )
        BookingCancellation.objects.get_or_create(
            booking=cancelled_b,
            defaults={'cancelled_by': student_rahul, 'reason': "Midterm exam was moved to 11:00 AM"}
        )

        # -------------------------------------------------------------
        # 14. Completed Payment Records
        # -------------------------------------------------------------
        paid_booking = Booking.objects.filter(facility__booking_price__gt=0).first()
        if paid_booking:
            Payment.objects.get_or_create(
                booking=paid_booking,
                defaults={
                    'user': paid_booking.user,
                    'amount': paid_booking.facility.booking_price,
                    'currency': 'INR',
                    'status': Payment.STATUS_COMPLETED,
                    'payment_method': Payment.METHOD_CAMPUS_CARD,
                    'notes': 'Smart campus ID auto-debit'
                }
            )

        self.stdout.write(self.style.SUCCESS("✓ 25+ Historical, checked-in, pending, and upcoming reservations loaded."))
        self.stdout.write(self.style.SUCCESS("✓ Real-world reviews, complaints, announcements, and maintenance windows seeded."))

        self.stdout.write(self.style.SUCCESS("\n======================================================="))
        self.stdout.write(self.style.SUCCESS("UniBook (CampusEase) Rich Demo Data Populated!"))
        self.stdout.write(self.style.SUCCESS("======================================================="))
        self.stdout.write("Credentials:")
        self.stdout.write("  - Super Admin:      admin          / AdminPass123!")
        self.stdout.write("  - Facility Manager: manager_demo   / ManagerPass123!")
        self.stdout.write("  - Sports Manager:   manager_sports / ManagerPass123!")
        self.stdout.write("  - Faculty:          faculty_demo   / FacultyPass123!")
        self.stdout.write("  - Student:          student_demo   / StudentPass123!")
        self.stdout.write("  - Student 2:        student_rahul  / StudentPass123!")
        self.stdout.write("=======================================================\n")
