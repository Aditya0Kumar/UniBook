from .models import Notification, Announcement


def notifications_context(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )[:5]
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        recent_announcements = Announcement.objects.filter(
            is_active=True
        )[:3]
        return {
            'header_notifications': unread_notifications,
            'unread_notifications_count': unread_count,
            'campus_announcements': recent_announcements,
        }
    return {
        'header_notifications': [],
        'unread_notifications_count': 0,
        'campus_announcements': Announcement.objects.filter(is_active=True)[:3],
    }

