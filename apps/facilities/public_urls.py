from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('facilities/', views.facility_directory_view, name='directory'),
    path('facilities/<slug:slug>/', views.facility_detail_view, name='facility_detail'),
]

