from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Department, UserProfile
from .serializers import UserSerializer, RegisterSerializer, DepartmentSerializer
from .permissions import IsSuperAdmin

User = get_user_model()

SELF_REGISTER_ROLES = (User.ROLE_STUDENT, User.ROLE_FACULTY)


def _safe_next_url(request):
    """Return the ?next= target only if it points back to this site."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


# -------------------------------------------------------------
# Template Views
# -------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('public:home')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Authenticate by username or email
        user = authenticate(request, username=username_or_email, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = _safe_next_url(request)
            if next_url:
                return redirect(next_url)
            
            # Role-based landing redirects
            if user.role == User.ROLE_ADMIN or user.is_superuser:
                return redirect('admin_panel:dashboard')
            elif user.role == User.ROLE_FACILITY_MANAGER:
                return redirect('staff:dashboard')
            elif user.role == User.ROLE_FACULTY:
                return redirect('faculty:dashboard')
            else:
                return redirect('student:dashboard')
        else:
            messages.error(request, "Invalid credentials. Please verify your username/email and password.")

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('public:home')

    departments = Department.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        university_id = request.POST.get('university_id', '').strip()
        role = request.POST.get('role', User.ROLE_STUDENT)
        department_id = request.POST.get('department')
        phone_number = request.POST.get('phone_number', '').strip()

        # Only student and faculty accounts can be self-registered. Facility managers
        # and admins must be created by an administrator.
        if role not in SELF_REGISTER_ROLES:
            messages.error(request, "Please choose a valid campus role.")
            return render(request, 'accounts/register.html', {'departments': departments})

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html', {'departments': departments})

        try:
            validate_password(password, user=User(username=username, email=email, first_name=first_name, last_name=last_name))
        except DjangoValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return render(request, 'accounts/register.html', {'departments': departments})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/register.html', {'departments': departments})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'accounts/register.html', {'departments': departments})

        department = Department.objects.filter(id=department_id).first() if department_id else None

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            university_id=university_id or None,
            role=role,
            department=department,
            phone_number=phone_number
        )
        login(request, user)
        messages.success(request, f"Registration successful! Welcome to UniBook, {user.first_name or user.username}.")
        if user.role == 'faculty':
            return redirect('faculty:dashboard')
        return redirect('student:dashboard')

    return render(request, 'accounts/register.html', {'departments': departments})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('public:home')


@login_required
def profile_view(request):
    user = request.user
    departments = Department.objects.all()

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        dept_id = request.POST.get('department')
        if dept_id:
            user.department = Department.objects.filter(id=dept_id).first()

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()

        # Update profile bio & emergency contact
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.emergency_contact = request.POST.get('emergency_contact', profile.emergency_contact)
        profile.academic_level = request.POST.get('academic_level', profile.academic_level)
        profile.save()

        messages.success(request, "Your profile details have been updated successfully.")
        return redirect('accounts:profile')

    return render(request, 'student/profile.html', {'departments': departments})


# -------------------------------------------------------------
# REST API Views
# -------------------------------------------------------------

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('department', 'profile')
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'university_id']
    ordering_fields = ['date_joined', 'username', 'role']
