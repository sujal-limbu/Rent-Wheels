from .models import Notification


def send_notification(user, title, message, notif_type='general'):
    Notification.objects.create(
        user       = user,
        title      = title,
        message    = message,
        notif_type = notif_type,
    )