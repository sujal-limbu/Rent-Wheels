from vehicles.models import Vehicle


def navbar_context(request):
    context = {}
    if request.user.is_authenticated:
        context['is_vehicle_owner'] = Vehicle.objects.filter(owner=request.user).exists()
    return context