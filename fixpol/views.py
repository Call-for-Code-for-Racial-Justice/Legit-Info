from django.shortcuts import render, redirect
from .models import Location, Impact, Criteria, Law
from .models import impact_seq, find_criteria_id
from .forms import SearchForm
from django.contrib.auth.models import User
from users.models import Profile

from django.http import HttpResponse
from django.core.mail import send_mail

# Debugging options
# return HttpResponse({variable to inspect})
# print {variable to inspect}
# raise Exception({variable to inspect})
# import pdb; pdb.set_trace()


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
    """Show search form to specify criteria."""
    crit = None
    
    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.
        if request.user.is_anonymous:
            form = SearchForm()             # blank search form
        else:
            crit = request.user.profile.criteria
            form = SearchForm(instance=crit)  # pre-filled with profile

    else:
        # POST data submitted; process data.
        
        form = SearchForm(data=request.POST)      
        if form.is_valid():
            criteria = form.save()
            crit_text = criteria.set_text()
            crit_id = find_criteria_id(crit_text)
            print(crit_id, crit_text)
            if crit_id == 0:
                criteria.save()
                crit_id = criteria.id
            return redirect('fixpol:results', search_id=crit_id)

    context = { 'form': form }
    return render(request, 'search.html', context)


def results(request, search_id):
    """Show search results."""
    criteria = Criteria.objects.get(id=search_id)
    loc = criteria.location
    impact_list = criteria.impacts.all()

    laws = Law.objects.filter(location=loc)
    laws = laws.filter(impact__in=impact_list)

    context = { 'heading': criteria.text,
                'laws' : laws} 
    return render(request, 'results.html', context)


def criteria(request, search_id):
    """Show search criteria."""
    criteria = Criteria.objects.get(id=search_id)
    context = {'criteria': criteria}
    return render(request, 'criteria.html', context)


def zero_if_none(item):
    """If item exists, return id, otherwise return 0."""
    result_id = 0
    #import pdb; pdb.set_trace()
    if item:
        result_id = item.id
    return result_id


def criterias(request):
    """Show all saved search criterias."""
    
    users = User.objects.order_by('id')
    profiles = Profile.objects.order_by('id')
    prof = []
    for profile in profiles:
        impact_string2 = impact_seq(profile.impacts.all())
        prof.append([profile.id, profile.location, 
                    impact_string2, zero_if_none(profile.criteria)])

    criterias = Criteria.objects.order_by('id')
    crit = []
    for criteria in criterias:
        impact_string3 = impact_seq(criteria.impacts.all())
        crit.append([criteria.id, criteria.text, 
                    criteria.location, impact_string3])

    context = { 'users': users,
                'prof': prof,
                'crit': crit}
    return render(request, 'criterias.html', context)


def sendmail(request):
    """ send results to profile user """

# subject: A string;
# message: A string;
# from_email: A string;
# recipient_list: A list of strings;
# fail_silently: A boolean;
# auth_user: The optional username to use to authenticate to the SMTP server;
# auth_password: The optional password to use to authenticate to the SMTP server;
# connection: The optional email backend to use to send the mail;
# html_message: An optional string containg the messsage in HTML format.


    send_mail(
        'Subject',
        'Email message',
        'tpearson@us.ibm.com',
        ['az990tony@gmail.com'],
        fail_silently=False,
    )

    return HttpResponse('Mail successfully sent')


def share(request):
    return render(request, 'share.html')

   

