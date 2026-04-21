from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    NOTIF_TYPES = [
        ('booking', 'Booking'),
        ('payment', 'Payment'),
        ('reminder', 'Reminder'),
        ('general', 'General'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='general')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"