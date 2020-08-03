from django.shortcuts import render
from .models import Location

# Create your views here.
def index(request):
    """The home page for Fix Politics."""

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = LocationForm()
    else:
        # POST data submitted; process data.
        form = LocationForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('impacts')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'index.html', context)


def locations(request):
    """Show all locations."""
    locations = Location.objects.order_by('date_added')
    context = {'locations': locations}
    return render(request, 'locations.html', context)
