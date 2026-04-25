from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    unread = notifications.filter(is_read=False).count()

    return render(request, 'notifications/notifications.html', {
        'notifications': notifications,
        'unread': unread,
    })


@login_required
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notifications')


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')