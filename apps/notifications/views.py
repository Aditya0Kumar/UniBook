from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification, Announcement


@login_required
def notification_list_view(request):
    # Evaluate the list first so the page can still highlight what was unread,
    # then mark everything as read for the next visit.
    notifications = list(Notification.objects.filter(recipient=request.user))
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'student/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, id=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')
