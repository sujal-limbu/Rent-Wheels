from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    renter      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle     = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    start_date  = models.DateField()
    end_date    = models.DateField()
    total_days  = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.renter.username} → {self.vehicle.title}"

    def save(self, *args, **kwargs):
        self.total_days = (self.end_date - self.start_date).days
        self.total_price = self.total_days * self.vehicle.price_per_day
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    booking         = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    esewa_ref_id    = models.CharField(max_length=100, blank=True)
    status          = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    paid_at         = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for {self.booking} - {self.status}"