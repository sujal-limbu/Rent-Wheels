from django.shortcuts import render
from .models import Vehicle

def home(request):
    featured_vehicles = Vehicle.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'featured_vehicles': featured_vehicles})