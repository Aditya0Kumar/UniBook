from django.urls import path
from . import dashboard_views

app_name = 'student'

urlpatterns = [
    path('dashboard/', dashboard_views.student_dashboard, name='dashboard'),
]
