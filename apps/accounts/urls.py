from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user-api')  # super admins only
router.register(r'departments', views.DepartmentViewSet, basename='department-api')

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
    path('api/', include(router.urls)),
]

