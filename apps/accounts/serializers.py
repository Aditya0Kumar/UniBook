from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Department, UserProfile

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['academic_level', 'bio', 'emergency_contact', 'notification_preferences']


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    profile = UserProfileSerializer(read_only=True)
    is_student = serializers.BooleanField(read_only=True)
    is_faculty = serializers.BooleanField(read_only=True)
    is_facility_manager = serializers.BooleanField(read_only=True)
    is_superadmin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'university_id', 'role', 'department', 'department_name',
            'phone_number', 'profile_picture', 'profile', 'date_joined',
            'is_student', 'is_faculty', 'is_facility_manager', 'is_superadmin'
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    # Self-registration is limited to students and faculty; managers/admins are
    # created by an administrator.
    role = serializers.ChoiceField(
        choices=[(User.ROLE_STUDENT, 'Student'), (User.ROLE_FACULTY, 'Faculty Member')],
        default=User.ROLE_STUDENT,
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'university_id', 'role', 'department', 'phone_number'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        candidate = User(
            username=attrs.get('username', ''),
            email=attrs.get('email', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

