from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('facilities/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('facilities/<slug:slug>/complaint/', views.submit_complaint, name='submit_complaint'),
]

