from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date
from .models import Vehicle, VehicleImage
from bookings.models import Booking


def home(request):
    featured_vehicles = Vehicle.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'featured_vehicles': featured_vehicles})


def vehicle_list(request):
    vehicles = Vehicle.objects.filter(is_available=True)

    vehicle_type = request.GET.get('type')
    location     = request.GET.get('location')
    min_price    = request.GET.get('min_price')
    max_price    = request.GET.get('max_price')
    fuel_type    = request.GET.get('fuel')
    seats        = request.GET.get('seats')

    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if location:
        vehicles = vehicles.filter(location__icontains=location)
    if min_price:
        vehicles = vehicles.filter(price_per_day__gte=min_price)
    if max_price:
        vehicles = vehicles.filter(price_per_day__lte=max_price)
    if fuel_type:
        vehicles = vehicles.filter(fuel_type=fuel_type)
    if seats:
        vehicles = vehicles.filter(seats=seats)

    context = {
        'vehicles'    : vehicles,
        'vehicle_type': vehicle_type,
        'location'    : location,
        'min_price'   : min_price,
        'max_price'   : max_price,
        'fuel_type'   : fuel_type,
        'seats'       : seats,
        'total'       : vehicles.count(),
    }
    return render(request, 'vehicles/vehicle_list.html', context)


def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    reviews = vehicle.reviews.all().order_by('-created_at')

    already_reviewed = False
    can_review       = False

    if request.user.is_authenticated:
        # ✅ Auto-complete expired bookings so review form unlocks immediately
        Booking.objects.filter(
            renter   = request.user,
            vehicle  = vehicle,
            status   = 'confirmed',
            end_date__lt = timezone.now().date(),
        ).update(status='completed')

        already_reviewed = vehicle.reviews.filter(reviewer=request.user).exists()
        has_completed    = Booking.objects.filter(
            renter  = request.user,
            vehicle = vehicle,
            status  = 'completed',
        ).exists()
        can_review = has_completed and not already_reviewed

    context = {
        'vehicle'         : vehicle,
        'reviews'         : reviews,
        'already_reviewed': already_reviewed,
        'can_review'      : can_review,
        'today'           : date.today().isoformat(),
    }
    return render(request, 'vehicles/vehicle_detail.html', context)


@login_required
def add_vehicle(request):
    if request.method == 'POST':
        vehicle = Vehicle.objects.create(
            owner         = request.user,
            title         = request.POST.get('title'),
            vehicle_type  = request.POST.get('vehicle_type'),
            brand         = request.POST.get('brand'),
            model         = request.POST.get('model'),
            year          = request.POST.get('year'),
            fuel_type     = request.POST.get('fuel_type'),
            seats         = request.POST.get('seats'),
            price_per_day = request.POST.get('price_per_day'),
            description   = request.POST.get('description'),
            location      = request.POST.get('location'),
            latitude      = request.POST.get('latitude') or 27.7172,
            longitude     = request.POST.get('longitude') or 85.3240,
        )
        for img in request.FILES.getlist('images'):
            VehicleImage.objects.create(vehicle=vehicle, image=img)

        messages.success(request, 'Vehicle listed successfully!')
        return redirect('vehicle_detail', pk=vehicle.pk)

    return render(request, 'vehicles/add_vehicle.html')


@login_required
def my_vehicles(request):
    vehicles = Vehicle.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'vehicles/my_vehicles.html', {'vehicles': vehicles})


@login_required
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted.')
    return redirect('my_vehicles')