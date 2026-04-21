from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle

class Review(models.Model):
    vehicle    = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reviews')
    reviewer   = models.ForeignKey(User, on_delete=models.CASCADE)
    rating     = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vehicle', 'reviewer')  # one review per person per vehicle

    def __str__(self):
        return f"{self.reviewer.username} → {self.vehicle.title} ({self.rating}★)"