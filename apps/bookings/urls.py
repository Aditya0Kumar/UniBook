from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'bookings'

router = DefaultRouter()
router.register(r'bookings', views.BookingViewSet, basename='booking-api')

urlpatterns = [
    # Template URLs
    path('facilities/<slug:slug>/book/', views.booking_create_view, name='booking_create'),
    path('my/', views.my_bookings_view, name='my_bookings'),
    path('<int:pk>/', views.booking_detail_view, name='booking_detail'),
    path('<int:pk>/qr/', views.booking_qr_view, name='booking_qr'),
    path('<int:pk>/cancel/', views.booking_cancel_view, name='booking_cancel'),

    # REST API endpoints
    path('api/', include(router.urls)),
]

