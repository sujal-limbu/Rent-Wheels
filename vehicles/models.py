from django.db import models
from django.contrib.auth.models import User

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('scooter', 'Scooter'),
        ('van', 'Van'),
        ('truck', 'Truck'),
    ]
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]

    owner         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    title         = models.CharField(max_length=200)
    vehicle_type  = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    brand         = models.CharField(max_length=100)
    model         = models.CharField(max_length=100)
    year          = models.IntegerField()
    fuel_type     = models.CharField(max_length=20, choices=FUEL_TYPES)
    seats         = models.IntegerField(default=5)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    description   = models.TextField()
    location      = models.CharField(max_length=200)
    latitude      = models.FloatField(default=27.7172)   # Default: Kathmandu
    longitude     = models.FloatField(default=85.3240)
    is_available  = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.owner.username}"

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0


class VehicleImage(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='vehicles/')

    def __str__(self):
        return f"Image for {self.vehicle.title}"