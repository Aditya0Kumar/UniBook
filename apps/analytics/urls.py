from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard_view, name='dashboard'),
    path('facilities/', views.admin_facilities_view, name='facilities'),
    path('users/', views.admin_users_view, name='users'),
    path('bookings/', views.admin_bookings_view, name='bookings'),
    path('maintenance/', views.admin_maintenance_view, name='maintenance'),
    path('complaints/', views.admin_complaints_view, name='complaints'),
    path('announcements/', views.admin_announcements_view, name='announcements'),
    path('payments/', views.admin_payments_view, name='payments'),
    path('export/bookings/csv/', views.admin_export_bookings_csv, name='export_bookings_csv'),
    path('export/facilities/csv/', views.admin_export_facilities_csv, name='export_facilities_csv'),
    path('api/analytics-data/', views.AdminAnalyticsAPIView.as_view(), name='api_analytics_data'),
]
