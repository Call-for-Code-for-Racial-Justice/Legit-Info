from django.shortcuts import render
from .models import Location, Impact

# Create your views here.
def index(request):
    """The home page for Fix Politics."""
    return render(request, 'index.html')

def locations(request):
    """Show all locations."""
    locations = Location.objects.order_by('date_added')
    locations = locations.exclude(desc='world')
    context = {'locations': locations}
    return render(request, 'locations.html', context)

def impacts(request):
    """Show all impacts."""
    impacts = Impact.objects.order_by('date_added')
    context = {'impacts': impacts}
    return render(request, 'impacts.html', context)
