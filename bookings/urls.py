from django.urls import path
from . import views
 
urlpatterns = [
    path('create/<int:vehicle_pk>/', views.create_booking, name='create_booking'),
    path('my/', views.my_bookings, name='my_bookings'),
    path('owner/', views.owner_bookings, name='owner_bookings'),  # ✅ Fix 4 — Owner dashboard
    path('detail/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('cancel/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    path('payment/initiate/<int:booking_pk>/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
]
 
