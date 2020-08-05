from django.shortcuts import render
from .models import Location, Impact, Criteria
from .forms import SearchForm

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

        form = SearchForm()
        if not request.user.is_anonymous:
            pre_fill = True
    else:
        # POST data submitted; process data.
        form = SearchForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('fixpol:results', search_id= id)

    context = { 'submit_form': form}
    return render(request, 'search.html', context)


def results(request, search_id):
    criteria = Criteria.objects.get(id=search_id)
    context = { 'location': criteria.location,
                'impact': criteria.impacts} 
    return render(request, 'results.html', context)

def share(request):
    return render(request, 'share.html')



