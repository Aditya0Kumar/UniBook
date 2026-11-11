from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification, Announcement


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all read on viewing list
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'student/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, id=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')
