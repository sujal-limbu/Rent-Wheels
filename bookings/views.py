from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from datetime import date
import uuid
from .models import Booking, Payment
from vehicles.models import Vehicle
from notifications.utils import send_notification


@login_required
def create_booking(request, vehicle_pk):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk, is_available=True)

    # ✅ Fix 1 — Owner cannot book their own vehicle
    if vehicle.owner == request.user:
        messages.error(request, 'You cannot book your own vehicle!')
        return redirect('vehicle_detail', pk=vehicle_pk)

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date   = request.POST.get('end_date')

        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end   = datetime.strptime(end_date,   '%Y-%m-%d').date()

        # Validations
        if start >= end:
            messages.error(request, 'End date must be after start date!')
            return redirect('vehicle_detail', pk=vehicle_pk)

        if start < date.today():
            messages.error(request, 'Start date cannot be in the past!')
            return redirect('vehicle_detail', pk=vehicle_pk)

        # Check overlapping bookings
        overlapping = Booking.objects.filter(
            vehicle=vehicle,
            status__in=['confirmed', 'active'],
            start_date__lt=end,
            end_date__gt=start,
        ).exists()

        if overlapping:
            messages.error(request, 'Vehicle is already booked for those dates!')
            return redirect('vehicle_detail', pk=vehicle_pk)

        # Create booking
        booking = Booking.objects.create(
            renter     = request.user,
            vehicle    = vehicle,
            start_date = start,
            end_date   = end,
        )

        # Create pending payment
        Payment.objects.create(
            booking = booking,
            amount  = booking.total_price,
        )

        # Notify renter
        send_notification(
            user    = request.user,
            title   = 'Booking Created!',
            message = f'Your booking for {vehicle.title} from {start} to {end} is pending payment.',
            notif_type = 'booking',
        )

        # Notify owner
        send_notification(
            user    = vehicle.owner,
            title   = 'New Booking Request!',
            message = f'{request.user.username} booked your {vehicle.title} from {start} to {end}.',
            notif_type = 'booking',
        )

        messages.success(request, 'Booking created! Please complete payment.')
        return redirect('booking_detail', pk=booking.pk)

    return redirect('vehicle_detail', pk=vehicle_pk)


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(renter=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)

    transaction_uuid = f"{booking.pk}-{int(booking.created_at.timestamp())}"
    signature = generate_esewa_signature(
        secret_key       = settings.ESEWA_SECRET_KEY,
        total_amount     = booking.total_price,
        transaction_uuid = transaction_uuid,
        product_code     = settings.ESEWA_MERCHANT_ID,
    )

    return render(request, 'bookings/booking_detail.html', {
        'booking'          : booking,
        'transaction_uuid' : transaction_uuid,
        'signature'        : signature,
        'esewa_merchant_id': settings.ESEWA_MERCHANT_ID,
        'esewa_success_url': settings.ESEWA_SUCCESS_URL,
        'esewa_failure_url': settings.ESEWA_FAILURE_URL,
    })


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            send_notification(
                user       = request.user,
                title      = 'Booking Cancelled',
                message    = f'Your booking for {booking.vehicle.title} has been cancelled.',
                notif_type = 'booking',
            )
            messages.success(request, 'Booking cancelled successfully.')
        else:
            messages.error(request, 'This booking cannot be cancelled.')
    return redirect('my_bookings')


@login_required
def initiate_payment(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk, renter=request.user)
    return render(request, 'bookings/esewa_payment.html', {
        'booking': booking,
        'esewa_merchant_id': settings.ESEWA_MERCHANT_ID,
        'esewa_success_url': settings.ESEWA_SUCCESS_URL,
        'esewa_failure_url': settings.ESEWA_FAILURE_URL,
    })


import json
import base64

def payment_success(request):
    data = request.GET.get('data')

    if not data:
        messages.error(request, 'No payment data received.')
        return redirect('my_bookings')

    try:
        # Decode the Base64 response from eSewa
        decoded     = base64.b64decode(data).decode('utf-8')
        esewa_data  = json.loads(decoded)

        status       = esewa_data.get('status')
        total_amount = esewa_data.get('total_amount')
        ref_id       = esewa_data.get('transaction_uuid')
        product_code = esewa_data.get('product_code')

        if status != 'COMPLETE':
            messages.error(request, 'Payment was not completed.')
            return redirect('my_bookings')

        # Find booking by transaction_uuid (we set it as booking.pk earlier)
        booking_pk = esewa_data.get('transaction_uuid', '').split('-')[0]
        booking    = Booking.objects.get(pk=booking_pk)
        payment    = booking.payment

        payment.status       = 'success'
        payment.esewa_ref_id = ref_id
        from django.utils import timezone
        payment.paid_at = timezone.now()
        payment.save()

        booking.status = 'confirmed'
        booking.save()

        booking.vehicle.is_available = False
        booking.vehicle.save()

        send_notification(
            user       = booking.renter,
            title      = '✅ Payment Successful!',
            message    = f'Payment of Rs {total_amount} confirmed for {booking.vehicle.title}.',
            notif_type = 'payment',
        )
        send_notification(
            user       = booking.vehicle.owner,
            title      = '💰 Payment Received!',
            message    = f'Payment received for {booking.vehicle.title} from {request.user.username}.',
            notif_type = 'payment',
        )

        messages.success(request, 'Payment successful!')
        return render(request, 'bookings/payment_success.html', {
            'ref_id': ref_id,
            'amt'   : total_amount,
        })

    except (Booking.DoesNotExist, Exception) as e:
        messages.error(request, f'Payment verification failed: {str(e)}')
        return redirect('my_bookings')


def payment_failure(request):
    messages.error(request, 'Payment failed or was cancelled.')
    return render(request, 'bookings/payment_failure.html')


# ✅ Fix 4 — Owner dashboard: see all incoming bookings on their vehicles
@login_required
def owner_bookings(request):
    my_vehicles = Vehicle.objects.filter(owner=request.user)
    bookings = Booking.objects.filter(
        vehicle__in=my_vehicles
    ).order_by('-created_at')
    return render(request, 'bookings/owner_bookings.html', {'bookings': bookings})

import hmac
import hashlib
import base64

def generate_esewa_signature(secret_key, total_amount, transaction_uuid, product_code):
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')