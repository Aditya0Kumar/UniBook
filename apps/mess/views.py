from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Meal, MealMenu, DietaryPreference
from apps.facilities.models import Facility


def mess_menu_view(request):
    mess_facilities = Facility.objects.filter(category__slug='mess-and-dining')
    selected_facility_id = request.GET.get('facility')
    if selected_facility_id:
        facility = mess_facilities.filter(id=selected_facility_id).first()
    else:
        facility = mess_facilities.first()

    menus = MealMenu.objects.filter(facility=facility).select_related('meal') if facility else []
    meals = Meal.objects.all()

    user_diet = None
    if request.user.is_authenticated:
        user_diet = DietaryPreference.objects.filter(user=request.user).first()
        if request.method == 'POST' and 'update_diet' in request.POST:
            pref = request.POST.get('preference', DietaryPreference.PREF_VEG)
            allergies = request.POST.get('allergies', '')
            DietaryPreference.objects.update_or_create(
                user=request.user,
                defaults={'preference': pref, 'allergies': allergies}
            )
            messages.success(request, "Dietary preferences updated.")
            return redirect('mess:menu')

    # Group menus by day_of_week
    days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    weekly_schedule = {}
    for day_idx, day_name in days_map.items():
        weekly_schedule[day_name] = [m for m in menus if m.day_of_week == day_idx]

    context = {
        'mess_facilities': mess_facilities,
        'selected_facility': facility,
        'meals': meals,
        'weekly_schedule': weekly_schedule,
        'user_diet': user_diet,
    }
    return render(request, 'public/mess_menu.html', context)
