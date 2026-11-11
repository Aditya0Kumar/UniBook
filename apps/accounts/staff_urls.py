from django.urls import path
from . import dashboard_views

app_name = 'staff'

urlpatterns = [
    path('dashboard/', dashboard_views.staff_dashboard, name='dashboard'),
    path('qr-scanner/', dashboard_views.staff_qr_scanner_view, name='qr_scanner'),
    path('approvals/', dashboard_views.staff_approvals_view, name='approvals'),
]

