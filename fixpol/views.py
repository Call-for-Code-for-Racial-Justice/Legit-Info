from django.shortcuts import render
from .models import Location, Impact
from .forms import SubmitForm

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
    """Show all impacts."""

    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.

        if request.user.is_anonymous:
            form = SubmitForm()
        else:
            form = SubmitForm()
    else:
        # POST data submitted; process data.
        form = SubmitForm(data=request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            a = cd.get('a')
            return redirect('fixpol:results', loc_id=7, impact_id=2)

    context = { 'submit_form': form}
    return render(request, 'search.html', context)


def results(request, loc_id, impact_id):
    location = Location.objects.get(id=loc_id)
    impact = Impact.objects.get(id=impact_id)
    context = { 'location': location,
                'impact': impact} 
    return render(request, 'results.html', context)

def share(request):
    return render(request, 'share.html')



