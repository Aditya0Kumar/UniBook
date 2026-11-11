"""
URL configuration for UniBook (CampusEase) project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # OpenAPI 3 / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Public Discovery & Landing Pages
    path('', include('apps.facilities.public_urls')),

    # Accounts & Authentication
    path('accounts/', include('apps.accounts.urls')),

    # Role Dashboards
    path('student/', include('apps.accounts.student_urls')),
    path('faculty/', include('apps.accounts.faculty_urls')),
    path('staff/', include('apps.accounts.staff_urls')),
    path('admin-panel/', include('apps.analytics.urls')),

    # Facilities & Bookings
    path('', include('apps.facilities.urls')),
    path('bookings/', include('apps.bookings.urls')),

    # Specialized Modules
    path('gym/', include('apps.gym.urls')),
    path('mess/', include('apps.mess.urls')),
    path('payments/', include('apps.payments.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('notifications/', include('apps.notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
