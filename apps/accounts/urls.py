from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Template Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # REST API Auth URLs
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api_login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
]
