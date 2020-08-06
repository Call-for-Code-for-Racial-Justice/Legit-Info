from django.shortcuts import render, redirect
from .models import Location, Impact, Criteria
from .forms import SearchForm
from django.contrib.auth.models import User
from users.models import Profile

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
    ARROW = r'&nbsp;&#8611;&nbsp;'

    profcrit = Criteria()
    if not request.user.is_anonymous:
        profcrit.location = request.user.profile.location
        for impact in request.user.profile.impacts.all():
            profcrit.impacts.add(impact)

    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.
        form = SearchForm(instance=profcrit)

    else:
        # POST data submitted; process data.
        form = SearchForm(data=request.POST, instance=profcrit)
        if form.is_valid():
            criteria = form.save(commit=False)
            text = criteria.location.hierarchy
            if text.startswith('world.'):
                text = text[5:].replace('.', ARROW)	
            criteria.text = text           
            criteria.save()
            return redirect('fixpol:results', search_id=criteria.id)

    context = { 'form': form }
    return render(request, 'search.html', context)


def results(request, search_id):
    criteria = Criteria.objects.get(id=search_id)
    context = { 'text': criteria.text} 
    return render(request, 'results.html', context)

def share(request):
    return render(request, 'share.html')

   

