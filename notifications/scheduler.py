from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def send_rental_reminders():
    """Notify renters 1 day before start and on the last day of rental."""
    from bookings.models import Booking
    from notifications.utils import send_notification

    today    = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    # ── 1 day before rental starts ────────────────────────────────────────────
    starting_tomorrow = Booking.objects.filter(
        status='confirmed',
        start_date=tomorrow,
    ).select_related('renter', 'vehicle')

    for booking in starting_tomorrow:
        from notifications.models import Notification
        already_sent = Notification.objects.filter(
            user=booking.renter,
            title__icontains='starts tomorrow',
            message__icontains=booking.vehicle.title,
        ).exists()

        if not already_sent:
            send_notification(
                user=booking.renter,
                title='⏰ Rental Starts Tomorrow!',
                message=(
                    f'Your rental of {booking.vehicle.title} starts tomorrow '
                    f'({booking.start_date}). Make sure you are ready for pickup!'
                ),
                notif_type='reminder',
            )
            logger.info(f'Start reminder sent to {booking.renter.username} for {booking.vehicle.title}')

    # ── On the last day of rental ─────────────────────────────────────────────
    ending_today = Booking.objects.filter(
        status__in=['confirmed', 'active'],
        end_date=today,
    ).select_related('renter', 'vehicle')

    for booking in ending_today:
        from notifications.models import Notification
        already_sent = Notification.objects.filter(
            user=booking.renter,
            title__icontains='ends today',
            message__icontains=booking.vehicle.title,
        ).exists()

        if not already_sent:
            send_notification(
                user=booking.renter,
                title='🔔 Rental Ends Today!',
                message=(
                    f'Your rental of {booking.vehicle.title} ends today '
                    f'({booking.end_date}). Please return the vehicle on time.'
                ),
                notif_type='reminder',
            )
            logger.info(f'End reminder sent to {booking.renter.username} for {booking.vehicle.title}')


def send_payment_reminders():
    """Nudge renters who have a pending booking older than 1 hour."""
    from bookings.models import Booking
    from notifications.utils import send_notification
    from notifications.models import Notification

    one_hour_ago = timezone.now() - timedelta(hours=1)

    pending_bookings = Booking.objects.filter(
        status='pending',
        created_at__lte=one_hour_ago,
    ).select_related('renter', 'vehicle')

    for booking in pending_bookings:
        already_sent = Notification.objects.filter(
            user=booking.renter,
            notif_type='payment',
            message__icontains=booking.vehicle.title,
            title__icontains='payment pending',
        ).exists()

        if not already_sent:
            send_notification(
                user=booking.renter,
                title='💳 Payment Pending!',
                message=(
                    f'Your booking for {booking.vehicle.title} is awaiting payment. '
                    f'Complete payment to confirm your booking before it expires.'
                ),
                notif_type='payment',
            )
            logger.info(f'Payment reminder sent to {booking.renter.username}')


def mark_completed_bookings():
    """Auto-complete bookings whose end date has passed."""
    from bookings.models import Booking
    from notifications.utils import send_notification

    today = timezone.localdate()

    expired = Booking.objects.filter(
        status__in=['confirmed', 'active'],
        end_date__lt=today,
    ).select_related('renter', 'vehicle')

    for booking in expired:
        booking.status = 'completed'
        booking.save()

        # Notify renter to leave a review
        send_notification(
            user=booking.renter,
            title='✅ Rental Completed!',
            message=(
                f'Your rental of {booking.vehicle.title} has been completed. '
                f'We hope you enjoyed it! Please leave a review.'
            ),
            notif_type='general',
        )

        # Make vehicle available again
        booking.vehicle.is_available = True
        booking.vehicle.save()

        logger.info(f'Booking #{booking.pk} marked as completed.')


def start():
    """Start the APScheduler. Called once from apps.py ready()."""
    scheduler = BackgroundScheduler(timezone='Asia/Kathmandu')

    # Rental reminders — every day at 8:00 AM Nepal time
    scheduler.add_job(
        send_rental_reminders,
        CronTrigger(hour=8, minute=0),
        id='rental_reminders',
        replace_existing=True,
    )

    # Payment reminders — every hour
    scheduler.add_job(
        send_payment_reminders,
        IntervalTrigger(hours=1),
        id='payment_reminders',
        replace_existing=True,
    )

    # Mark completed bookings — every day at midnight
    scheduler.add_job(
        mark_completed_bookings,
        CronTrigger(hour=0, minute=5),
        id='mark_completed',
        replace_existing=True,
    )

    scheduler.start()
    logger.info('RentWheels scheduler started.')