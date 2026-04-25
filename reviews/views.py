from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from vehicles.models import Vehicle
from bookings.models import Booking


@login_required
def add_review(request, vehicle_pk):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)

    if request.method != 'POST':
        return redirect('vehicle_detail', pk=vehicle_pk)

    # ✅ Only allow review if user has a completed booking for this vehicle
    has_completed_booking = Booking.objects.filter(
        renter=request.user,
        vehicle=vehicle,
        status='completed'
    ).exists()

    if not has_completed_booking:
        messages.error(request, 'You can only review vehicles you have rented.')
        return redirect('vehicle_detail', pk=vehicle_pk)

    # ✅ One review per person per vehicle
    if Review.objects.filter(vehicle=vehicle, reviewer=request.user).exists():
        messages.error(request, 'You have already reviewed this vehicle.')
        return redirect('vehicle_detail', pk=vehicle_pk)

    rating  = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not rating or not comment:
        messages.error(request, 'Please provide both a rating and a comment.')
        return redirect('vehicle_detail', pk=vehicle_pk)

    Review.objects.create(
        vehicle  = vehicle,
        reviewer = request.user,
        rating   = int(rating),
        comment  = comment,
    )

    messages.success(request, 'Review submitted successfully!')
    return redirect('vehicle_detail', pk=vehicle_pk)