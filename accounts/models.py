from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE)
    phone        = models.CharField(max_length=15, blank=True)
    address      = models.TextField(blank=True)
    profile_pic  = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified  = models.BooleanField(default=False)
    license_no   = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"