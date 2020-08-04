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

def search(request):
    """Add a new topic."""
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = FruitForm()
    else:
        # POST data submitted; process data.
        form = FruitForm(data=request.POST)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.owner = request.user
            new_topic.save()
            return redirect('fixpol:index')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'search.html', context)
