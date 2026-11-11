import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import Department, UserProfile
from apps.facilities.models import FacilityCategory, Facility, FacilityOperatingHour, Holiday
from apps.gym.models import Trainer, GymSession, GymMembership
from apps.mess.models import Meal, MealMenu, DietaryPreference
from apps.sports.models import Sport, SportsCourt, SportsEquipment
from apps.laboratories.models import Laboratory, LabEquipment
from apps.events.models import EventAuditoriumDetail
from apps.bookings.services import create_booking
from apps.bookings.models import Booking
from apps.notifications.models import Announcement, Notification
from apps.reviews.models import Review

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds complete realistic demo facilities, users, menus, and bookings into UniBook.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting UniBook demo data seeding..."))

        # 1. Departments
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
        self.stdout.write(self.style.SUCCESS("✓ Departments seeded."))

        # 2. Users for all 4 roles
        # A. Super Admin
        admin_user, created = User.objects.get_or_create(
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

        # B. Facility Manager
        manager_user, created = User.objects.get_or_create(
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

        # C. Faculty Member
        faculty_user, created = User.objects.get_or_create(
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

        # D. Student Member
        student_user, created = User.objects.get_or_create(
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

        self.stdout.write(self.style.SUCCESS("✓ Users created for Student, Faculty, Facility Manager, and Admin."))

        # 3. All 13 Facility Categories
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
        self.stdout.write(self.style.SUCCESS("✓ 13 Facility Categories configured."))

        # 4. Mandatory Facilities from Specification
        facilities_spec = [
            # 1 Gym
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
            },
            # 2 Mess Facilities
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
            },
            # 3 Badminton Courts
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
            },
            # 2 Basketball Courts
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
            },
            # 1 Football Ground
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
            },
            # 1 Swimming Pool
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
            },
            # 3 Laboratories
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
            },
            # 2 Auditoriums
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
            },
            # 3 Seminar Halls
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
            },
            # 2 Library Study Rooms
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
                    'assigned_manager': manager_user,
                    'facility_status': Facility.STATUS_ACTIVE
                }
            )
            created_facilities[f_data['slug']] = facility

            # Add default operating hours Monday to Sunday
            for day in range(7):
                FacilityOperatingHour.objects.get_or_create(
                    facility=facility,
                    day_of_week=day,
                    defaults={'opening_time': f_data['open'], 'closing_time': f_data['close'], 'is_closed': False}
                )

        self.stdout.write(self.style.SUCCESS("✓ 18 Mandated facilities created with operating schedules."))

        # 5. Gym Sessions and Trainers
        trainer1, _ = Trainer.objects.get_or_create(
            name='Coach Vikram Rao',
            defaults={
                'specialization': 'Strength & Conditioning',
                'bio': 'CSCS Certified with 8+ years experience preparing collegiate athletes and lifters.',
                'is_available': True
            }
        )
        trainer2, _ = Trainer.objects.get_or_create(
            name='Coach Sarah Jenkins',
            defaults={
                'specialization': 'HIIT & Mobility',
                'bio': 'Specializes in functional movement, flexibility, and cardiovascular endurance.',
                'is_available': True
            }
        )

        gym_fac = created_facilities.get('campus-central-gymnasium')
        if gym_fac:
            GymSession.objects.get_or_create(
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
            GymSession.objects.get_or_create(
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
            GymSession.objects.get_or_create(
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

        # 6. Mess Meals & Weekly Menus
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
            ]
            for day, m_type, dishes in menu_samples:
                MealMenu.objects.get_or_create(
                    facility=mess1,
                    day_of_week=day,
                    meal=created_meals[m_type],
                    defaults={'dishes': dishes, 'special_dietary_options': 'Jain and Vegan counters available'}
                )

        # 7. Sports Details & Equipment
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
            defaults={'total_quantity': 20, 'available_quantity': 16}
        )
        SportsEquipment.objects.get_or_create(
            sport=basketball_sport,
            name='Spalding Composite Leather Basketball',
            defaults={'total_quantity': 15, 'available_quantity': 12}
        )

        # 8. Lab Equipment
        ai_lab = created_facilities.get('advanced-ai-cloud-lab')
        if ai_lab:
            lab_prof, _ = Laboratory.objects.get_or_create(
                facility=ai_lab,
                defaults={'lab_type': Laboratory.LAB_COMPUTER, 'safety_guidelines': 'Secure lab pass required at entry.'}
            )
            LabEquipment.objects.get_or_create(
                laboratory=lab_prof,
                name='NVIDIA DGX A100 8-GPU Compute Station',
                defaults={'total_count': 4, 'available_count': 4}
            )

        # 9. Campus Announcements
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

        # 10. Reviews for popular facilities
        Review.objects.get_or_create(
            facility=created_facilities['badminton-court-1'],
            user=student_user,
            defaults={'rating': 5, 'comment': 'Superb teakwood floor! Lighting is bright and glare-free. Easy to book via UniBook.'}
        )
        Review.objects.get_or_create(
            facility=created_facilities['campus-central-gymnasium'],
            user=faculty_user,
            defaults={'rating': 5, 'comment': 'Clean locker rooms, modern equipment, and attentive trainers. Highly recommended.'}
        )

        # 11. Create Realistic Reservations
        today = timezone.localdate()
        tomorrow = today + datetime.timedelta(days=1)
        day_after = today + datetime.timedelta(days=2)

        try:
            # Booking 1: Confirmed student badminton booking tomorrow morning
            b1 = create_booking(
                user=student_user,
                facility_id=created_facilities['badminton-court-1'].id,
                booking_date=tomorrow,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
                participant_count=2,
                purpose="Friendly practice match before midterms"
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Sample Booking 1 created: {b1.booking_reference}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Booking 1 note: {e}"))

        try:
            # Booking 2: Pending faculty seminar hall booking
            b2 = create_booking(
                user=faculty_user,
                facility_id=created_facilities['seminar-hall-101'].id,
                booking_date=day_after,
                start_time=datetime.time(14, 0),
                end_time=datetime.time(15, 0),
                participant_count=35,
                purpose="Guest Lecture: Quantum Algorithms in Cryptography"
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Sample Booking 2 created: {b2.booking_reference}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Booking 2 note: {e}"))

        self.stdout.write(self.style.SUCCESS("\n======================================================="))
        self.stdout.write(self.style.SUCCESS("UniBook (CampusEase) Demo Data Successfully Populated!"))
        self.stdout.write(self.style.SUCCESS("======================================================="))
        self.stdout.write("Test User Credentials:")
        self.stdout.write("  - Super Admin:      admin        / AdminPass123!")
        self.stdout.write("  - Facility Manager: manager_demo / ManagerPass123!")
        self.stdout.write("  - Faculty:          faculty_demo / FacultyPass123!")
        self.stdout.write("  - Student:          student_demo / StudentPass123!")
        self.stdout.write("=======================================================\n")

