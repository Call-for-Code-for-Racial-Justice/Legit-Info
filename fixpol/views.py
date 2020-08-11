import os
import csv
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Location, Impact, Criteria, Law
from .models import impact_seq, find_criteria_id
from .forms import SearchForm
from django.contrib.auth.models import User
from users.models import Profile

from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from datetime import datetime
from django.conf import settings

# Debugging options
# return HttpResponse({variable to inspect})
# print {variable to inspect}
# raise Exception({variable to inspect})
# import pdb; pdb.set_trace()

RESULTSDIR = 'results'

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

def results_basename(search_id):
    basename = 'fixpol-results-{}.csv'.format(search_id)   
    return basename    


def results_filename(search_id):
    basename = results_basename(search_id)
    filename = os.path.join(settings.MEDIA_ROOT, basename) 
    return filename       


def make_csv(search_id, laws):
    laws_table = []
    for law in laws:
        laws_table.append({'key': law.key,
                        'location': law.location.desc, 
                        'impact': law.impact.text, 
                        'title': law.title, 
                        'summary': law.summary})

    filename = results_filename(search_id)       
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['key', 'location', 'impact', 'title', 'summary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for law in laws_table:
            writer.writerow(law)
    return None


def cte_query(loc):
    loc_list = [loc]
    base = loc.hierarchy
    for n in range(10):
        loc = loc.parent
        if loc:
            loc_list.append(loc)
            if loc.shortname == 'world':
                break
        else:
            break
    return loc_list


def results(request, search_id):
    """Show search results."""
    
    criteria = Criteria.objects.get(id=search_id)
    loc = criteria.location
    #import pdb; pdb.set_trace()
    loc_list = cte_query(loc)
    impact_list = criteria.impacts.all()

    laws = Law.objects.filter(location__in=loc_list)
    laws = laws.filter(impact__in=impact_list)

    gen_date = datetime.now().strftime("%B %-d, %Y")

    context = { 'heading': criteria.text,
                'laws' : laws,
                'numlaws': len(laws),
                'search_id': search_id, 
                'gen_date': gen_date} 

    make_csv(search_id, laws)
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


def strip_double_quotes(item):
    new_item = item
    if item.startswith('"') and item.endswith('"'):
        new_item = item[1:-1]
    return new_item


def recipient_format(first,last,addr):
    if first=='' and last=='':
        rec = addr
    else:
        rec = first+' '+last+' <'+addr+'>'
    return rec

def sendmail(request, search_id):
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

    
    today = datetime.now()
    gen_date = today.strftime("%B %d, %Y")

    filename = results_filename(search_id)
    with open(filename, 'rt') as res_file:
        resultsReader = csv.DictReader(res_file)
        laws_found = list(resultsReader)
        #import pdb; pdb.set_trace()

    subject = 'Fix Politics -- Legislation Search Results -- ' + gen_date
    sender_email = 'fix-politics-cfc@ibm.com'
    user = request.user
    recipients = [ recipient_format(user.first_name,
                                    user.last_name,
                                    user.email)]
    
    context = {'laws_found': laws_found}
    text_version = render_to_string(
            template_name='email-results.txt', 
            context=context, request=request)
    html_version = render_to_string(
            template_name='email-results.html', 
            context=context, request=request)

    sent =  send_mail(subject, text_version, sender_email, recipients, 
            fail_silently=True, html_message=html_version)

    if sent > 0:
        status_message = 'Mail successfully sent to:'
    else:
        status_message = 'ERROR: Unable to deliver email' 
    

    context = { 'status_message': status_message,
                'recipients': recipients, 
                'search_id': search_id}
    return render(request, 'email_sent.html', context)


def share(request):
    return render(request, 'share.html')

   
def download(request, search_id):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    basename = results_basename(search_id)
    disp = 'attachment; filename="{}"'.format(basename)
    response['Content-Disposition'] = disp
    writer = csv.writer(response)
    with open(results_filename(search_id), newline="") as in_file:
        reader = csv.reader(in_file)
        for row in reader:
            writer.writerow(row)
    return response

def health(request):
    state = {"status": "UP"}
    return JsonResponse(state)