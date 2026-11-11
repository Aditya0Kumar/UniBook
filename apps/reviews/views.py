from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.facilities.models import Facility
from .models import Review, Complaint


@login_required
def submit_review(request, slug):
    facility = get_object_or_404(Facility, slug=slug)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '').strip()

        Review.objects.update_or_create(
            facility=facility,
            user=request.user,
            defaults={'rating': rating, 'comment': comment, 'is_approved': True}
        )
        messages.success(request, f"Thank you! Your review for {facility.name} has been published.")

    return redirect('public:facility_detail', slug=facility.slug)


@login_required
def submit_complaint(request, slug):
    facility = get_object_or_404(Facility, slug=slug)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if title and description:
            Complaint.objects.create(
                facility=facility,
                user=request.user,
                title=title,
                description=description
            )
            messages.success(request, "Your report has been submitted to the Facility Administrator.")
        else:
            messages.error(request, "Please provide both a title and description.")

    return redirect('public:facility_detail', slug=facility.slug)
