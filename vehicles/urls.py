from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('add/', views.add_vehicle, name='add_vehicle'),
    path('my/', views.my_vehicles, name='my_vehicles'),
    path('delete/<int:pk>/', views.delete_vehicle, name='delete_vehicle'),
]