from django.urls import path
from . import views

app_name = 'gym'

urlpatterns = [
    path('', views.gym_overview_view, name='overview'),
]

