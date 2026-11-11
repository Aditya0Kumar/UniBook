from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trainer, GymSession, GymMembership
from apps.facilities.models import Facility


def gym_overview_view(request):
    facility = Facility.objects.filter(category__slug='gym').first()
    sessions = GymSession.objects.filter(facility=facility) if facility else GymSession.objects.all()
    trainers = Trainer.objects.filter(is_available=True)
    
    user_membership = None
    if request.user.is_authenticated:
        user_membership = GymMembership.objects.filter(user=request.user, is_active=True).first()

    context = {
        'facility': facility,
        'sessions': sessions,
        'trainers': trainers,
        'user_membership': user_membership,
    }
    return render(request, 'public/gym_overview.html', context)
