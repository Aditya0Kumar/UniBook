from django.urls import path
from . import dashboard_views

app_name = 'faculty'

urlpatterns = [
    path('dashboard/', dashboard_views.faculty_dashboard, name='dashboard'),
]

