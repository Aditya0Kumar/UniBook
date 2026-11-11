# UniBook (CampusEase) 🎓
### University Facility Booking & Operational Resource Management System
**Built with Python 3.12+ &bull; Django 5/6 &bull; Django REST Framework &bull; MySQL 8+ &bull; WhiteNoise &bull; FullCalendar &bull; Chart.js**

---

## 🌟 Executive Overview

**UniBook** is an enterprise-grade university facility reservation and resource management web application designed for campus environments. It empowers **Students**, **Faculty Members**, **Facility Managers**, and **Super Administrators** to discover, schedule, validate, and manage university assets—including Olympic athletic complexes, research laboratories, dining messes, auditoriums, seminar halls, and study pods—in real-time with zero double-booking conflicts and touchless QR entry validation.

---

## 🏗️ Architecture & Modular App Structure

The platform adopts a decoupled, domain-driven modular Django architecture:

```
UniBook/
├── config/                 # Project settings, URL routing, ASGI/WSGI
│   ├── settings.py         # MySQL/SQLite, JWT, WhiteNoise, DRF, Spectacular
│   ├── urls.py             # Global endpoints, Swagger UI, media & static
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/           # CustomUser, UserProfile, Department, Roles & Dashboards
│   ├── facilities/         # Categories (13), Facilities (18+), Operating Hours, Holidays
│   ├── bookings/           # Concurrency Engine (select_for_update), Bookings, QR Generator
│   ├── gym/                # Gym Sessions, Memberships, Certified Trainers, Occupancy
│   ├── mess/               # Dining Halls, Weekly Food Menus, Dietary Preferences, Passes
│   ├── sports/             # Courts (Wooden/Synthetic/Turf), Equipment Rental & Allocation
│   ├── laboratories/       # GPU Clusters, Robotics, Cleanrooms, Faculty Supervisions
│   ├── events/             # Auditorium Specs, AV Requirements, Symposium Workflows
│   ├── payments/           # Smart ID Card deductions, Razorpay Gateway test simulation
│   ├── notifications/      # Real-time In-App alerts, Campus Announcements, Reminders
│   ├── maintenance/        # Facility Downtime Windows & Schedule Interlocks
│   ├── reviews/            # Verified Star Ratings, Student Reviews & Complaint Tracking
│   └── analytics/          # Chart.js Data Aggregations, Audit Logs, CSV Export Reports
├── templates/              # Inter UI, Bootstrap 5, HTMX, Lucide Icons
│   ├── base.html           # Unified responsive navigation & unread notifications dropdown
│   ├── public/             # Landing page, Directory, Detail + FullCalendar + Booking modal
│   ├── student/            # Student Dashboard, My Bookings, Passes, Checkout, Profile
│   ├── faculty/            # Academic Facility Booking, Recurring Semester Privileges
│   ├── staff/              # Operations Portal, Real-time QR Camera Scanner, Approvals
│   ├── admin_panel/        # Super Admin KPI Dashboard, Analytics Charts, User & Facility Tables
│   └── accounts/           # Sign In & Registration with One-Click Demo Credentials
├── static/                 # CSS, JavaScript, Static Assets
├── media/                  # Facility Photos, Generated QR Pass PNGs, User Profiles
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚡ Key Technical Capabilities

### 1. Robust Concurrency & Conflict Prevention
- **Database Row Locking (`select_for_update()`)**: Guarantees atomic reservation transactions under heavy concurrent user requests.
- **Exclusive vs. Shared Facilities**:
  - *Exclusive facilities* (e.g., Badminton Courts, Seminar Halls, Auditoriums): Strictly blocks overlapping reservations.
  - *Shared facilities* (e.g., Gym, Mess): Dynamically computes aggregate participant counts and enforces strict capacity limits.
- **Operating Schedule & Maintenance Interlocks**: Automatically rejects bookings requested during scheduled maintenance periods, past time slots, university holidays, or outside operating hours.

### 2. Touchless QR Pass & Replay-Resistant Check-in
- Confirmed reservations generate a cryptographic token stored in a high-resolution QR image.
- Facility Managers use an in-browser camera scanner (or manual token lookup) to validate passes.
- Instant checks ensure:
  - Token and reservation reference validity.
  - Active date verification (prevents using passes on the wrong day).
  - **Duplicate / Replay Check-in Prevention**: Flags and rejects passes that have already been validated.

### 3. Four Role-Specific Dashboards
- **Student Dashboard (`/student/dashboard/`)**: Active booking summaries, upcoming entry passes, quick-book shortcuts for gym and mess, notices.
- **Faculty Portal (`/faculty/dashboard/`)**: Direct booking of advanced research and computing laboratories, special recurring weekly reservation privileges.
- **Facility Manager Portal (`/staff/dashboard/`)**: Real-time QR camera scanner, pending approval actions, today's arrivals schedule, maintenance status.
- **Super Admin Operations (`/admin-panel/`)**: High-level platform KPIs, interactive Chart.js analytics (Daily trends, Category demand, Peak booking hours), CSV report exports, user directory, and audit logs.

### 4. RESTful API & Swagger / OpenAPI Documentation
- Fully documented interactive API interface powered by `drf-spectacular` at `/api/docs/`.
- SimpleJWT authentication with Token Obtain (`/accounts/api/auth/login/`) and Token Refresh.
- Clean CRUD endpoints with filtering, search, and pagination.

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.12+ (or 3.14+)
- MySQL Server 8.0+ (Optional for local development; system gracefully defaults to zero-config SQLite if MySQL is not specified)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/your-repo/UniBook.git
cd UniBook

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```ini
DEBUG=True
SECRET_KEY=unibook-production-secure-key-2026

# To connect to MySQL 8:
DB_ENGINE=mysql
DB_NAME=unibook_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Or leave DB_ENGINE=sqlite for local development
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Demo Campus Data
Run the built-in management command to automatically populate all 13 categories, 18 mandatory campus facilities, operating schedules, gym sessions, weekly menus, and accounts:
```bash
python manage.py seed_demo
```

### 5. Run the Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 🔑 Demo User Credentials

The seed command creates active test accounts for all user roles:

| Role | Username | Password | Email | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | `admin` | `AdminPass123!` | `admin@unibook.campus.edu` | Full platform control, Analytics, Export CSV, Audit logs |
| **Facility Manager** | `manager_demo` | `ManagerPass123!` | `manager@unibook.campus.edu` | QR Entrance Scanner, Approvals, Facility operations |
| **Faculty Member** | `faculty_demo` | `FacultyPass123!` | `faculty@unibook.campus.edu` | Academic labs, recurring semester reservations |
| **Student** | `student_demo` | `StudentPass123!` | `student@unibook.campus.edu` | Book facilities, view QR passes, submit reviews |

*(The Sign In page also includes one-click demo autofill buttons for fast testing).*

---

## 🧪 Automated Test Suite

UniBook includes a comprehensive test suite covering concurrency protection, double-booking prevention, capacity limits, cancellations, QR check-ins, and REST APIs:

```bash
python manage.py test apps.bookings
```

Output:
```
Ran 10 tests in 46.707s
OK
```

---

## 📡 Core API Reference

- **Interactive Swagger UI**: `GET /api/docs/`
- **OpenAPI Schema**: `GET /api/schema/`
- **Auth Token (JWT)**: `POST /accounts/api/auth/login/`
- **Token Refresh**: `POST /accounts/api/auth/token/refresh/`
- **Facilities List**: `GET /api/facilities/`
- **Facility Availability**: `GET /api/facilities/<id>/availability/?date=YYYY-MM-DD`
- **Calendar Events**: `GET /api/facilities/<id>/calendar-events/?start=...&end=...`
- **Create Booking**: `POST /bookings/api/bookings/`
- **My Bookings**: `GET /bookings/api/bookings/my/`
- **Cancel Booking**: `POST /bookings/api/bookings/<id>/cancel/`
- **Approve Booking**: `POST /bookings/api/bookings/<id>/approve/`
- **Reject Booking**: `POST /bookings/api/bookings/<id>/reject/`
- **QR Check-in**: `POST /bookings/api/bookings/check-in/`
- **Analytics Data**: `GET /admin-panel/api/analytics-data/`

---

## 🌐 Production Deployment Guide

1. **Static Files**: Pre-configured with WhiteNoise compression and caching:
   ```bash
   python manage.py collectstatic --noinput
   ```
2. **Database**: Use a managed MySQL 8 instance on AWS RDS, DigitalOcean, or Railway. Set `DB_ENGINE=mysql` in environment variables.
3. **WSGI Server**: Run with Gunicorn:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4
   ```

---

## 📄 License
Academic and Commercial Open License &copy; 2026 UniBook Project. Developed for university campus operations.
