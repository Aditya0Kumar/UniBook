from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'facilities'

router = DefaultRouter()
router.register(r'facilities', views.FacilityViewSet, basename='facility-api')
router.register(r'categories', views.FacilityCategoryViewSet, basename='category-api')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/facilities/<int:pk>/availability/', views.FacilityAvailabilityAPIView.as_view(), name='facility-availability-api'),
    path('api/facilities/<int:pk>/calendar-events/', views.FacilityCalendarEventsAPIView.as_view(), name='facility-calendar-events-api'),
]

