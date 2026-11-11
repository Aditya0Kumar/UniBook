from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:booking_id>/', views.payment_checkout_view, name='checkout'),
]

