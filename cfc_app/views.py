# views.py
import csv
from datetime import datetime
import os

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

from users.models import Profile
from .models import Location, Impact, Criteria, Law
from .models import impact_seq
from .forms import SearchForm

# Debugging options
# return HttpResponse({variable to inspect})
# print {variable to inspect}
# raise Exception({variable to inspect})
# import pdb; pdb.set_trace()

#########################
# Support functions here
#########################


def cte_query(loc):
    """ Ancestor-search, find all parents to specified location"""
    loc_list = [loc]
    for n in range(10):
        loc = loc.parent
        if loc:
            loc_list.append(loc)
            if loc.shortname == 'world':
                break
        else:
            break
    return loc_list


def load_default_impacts():
    # The 'None' option allows legislation to be hidden from all
    # searches.  This is useful for legislation that is fetched
    # through automation but mis-classified.  Setting impact=None
    # will prevent automation from fetching updated versions of this.

    # Impacts are displayed in the order they are added in this table.
    # Any new impacts added will appear at the bottom of the list.
    default_impacts = ['None', 'Healthcare', 'Safety', 'Environment',
                       'Transportation', 'Jobs']
    for entry in default_impacts:
        new_impact = Impact()
        new_impact.text = entry
        new_impact.save()
    return None


def load_default_locations():
    # The 'world' entry points to itself, so cannot be added using
    # traditional Django administration.  To create it here, we have
    # to create an entry with no parent, save it, then set the parent_id
    # to 1.  This only works if the AUTOINCREMENT sequence is set to zero,
    # for an empty database, or reset to zero if entries deleted.

    world = Location()
    world.desc = 'world'
    world.shortname = 'world'
    world.legiscan_id = 0
    world.hierarchy = 'world'
    world.govlevel = 'world'
    world.save()
    world.parent_id = 1
    world.save()

    # The concept of ancestor-search is confusing, so we create a few
    # entries (usa, arizona, ohio) so people can understand the structure
    # Note the legiscan_id is only needed for States in the United States.

    usa = Location(desc='United States', shortname='usa', legiscan_id = 52,
                   hierarchy='world.usa', govlevel='country')
    usa.parent = world
    usa.save()

    arizona = Location(desc='Arizona, USA', shortname='az', legiscan_id = 3,
                       hierarchy='world.usa.az', govlevel='state')
    arizona.parent = usa
    arizona.save()

    ohio = Location(desc='Ohio, USA', shortname='oh', legiscan_id = 35,
                    hierarchy='world.usa.oh', govlevel='state')
    ohio.parent = usa
    ohio.save()
    return None


def make_csv(search_id, laws):
    """ Make Comma-Separated-Value (CSV) format file"""
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


def recipient_format(first, last, addr):
    """ Format receiption with email address and name if available """
    if first == '' and last == '':
        rec = addr
    else:
        rec = first+' '+last+' <'+addr+'>'
    return rec


def results_basename(search_id):
    """ Generate the base name for the download file """
    basename = 'results-{}.csv'.format(search_id)
    return basename


def results_filename(search_id):
    """ Generate the fully qualified name for results file """
    basename = results_basename(search_id)
    filename = os.path.join(settings.MEDIA_ROOT, basename)
    return filename


def strip_double_quotes(item):
    """ Remove double quotes and the beginning and end of string """
    new_item = item
    if item.startswith('"') and item.endswith('"'):
        new_item = item[1:-1]
    return new_item


def zero_if_none(item):
    """If item exists, return id, otherwise return 0."""
    result_id = 0
    # import pdb; pdb.set_trace()
    if item:
        result_id = item.id
    return result_id

#########################
# Create your views here.
#########################


def criteria(request, search_id):
    """Show search criteria."""
    criteria = Criteria.objects.get(id=search_id)
    context = {'criteria': criteria}
    return render(request, 'criteria.html', context)


@staff_member_required
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

    context = {'users': users,
               'prof': prof,
               'crit': crit}
    return render(request, 'criterias.html', context)


def download(request, search_id):
    """ Download results as CSV file """

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
    """ Used by Docker/Tekton to confirm status """

    state = {"status": "UP"}
    return JsonResponse(state)


def impacts(request):
    """Show all impacts."""
    impacts = Impact.objects.order_by('date_added')
    if len(impacts) == 0:
        load_default_impacts()

    # Do not display the None option for end-users
    impacts = Impact.objects.order_by('date_added').exclude(text='None')

    context = {'impacts': impacts}
    return render(request, 'impacts.html', context)


def index(request):
    """The home page for this application."""
    return render(request, 'index.html')


@staff_member_required
def lawdump(request):
    """ Download all legislation as CSV file, for staff use only """

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    basename = 'lawdump.csv'
    disp = 'attachment; filename="{}"'.format(basename)
    response['Content-Disposition'] = disp
    writer = csv.writer(response)
    writer.writerow(['key', 'location', 'impact', 'title', 'summary'])
    for law in Law.objects.all():
        writer.writerow([law.key, law.location.desc, law.impact.text,
                         law.title, law.summary])
    return response


def locations(request):
    """Show all locations."""
    locations = Location.objects.order_by('hierarchy')

    # If database is empty, re-create the "world" entry that acts as
    # the master parent for the ancestor-search.
    if len(locations) == 0:
        load_default_locations()

    locations = Location.objects.order_by('hierarchy').exclude(desc='world')
    context = {'locations': locations}
    return render(request, 'locations.html', context)


def results(request, search_id):
    """Show search results."""

    criteria = Criteria.objects.get(id=search_id)
    loc = criteria.location
    # import pdb; pdb.set_trace()
    loc_list = cte_query(loc)
    impact_list = criteria.impacts.all()

    laws = Law.objects.filter(location__in=loc_list)
    laws = laws.filter(impact__in=impact_list)

    gen_date = datetime.now().strftime("%B %-d, %Y")

    context = {'heading': criteria.text,
               'laws': laws,
               'numlaws': len(laws),
               'search_id': search_id,
               'gen_date': gen_date}

    make_csv(search_id, laws)
    return render(request, 'results.html', context)


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
            criteria.set_text()
            criteria.save()
            crit_id = criteria.id
            return redirect('cfc_app:results', search_id=crit_id)

    context = {'form': form}
    return render(request, 'search.html', context)


def sendmail(request, search_id):
    """ send results to profile user """

# subject: A string;
# message: A string;
# from_email: A string;
# recipient_list: A list of strings;
# fail_silently: A boolean;
# auth_user: The optional username to use to authenticate to the SMTP server;
# auth_password: optional password to use to authenticate to the SMTP server;
# connection: The optional email backend to use to send the mail;
# html_message: An optional string containg the messsage in HTML format.

    today = datetime.now()
    gen_date = today.strftime("%B %d, %Y")

    # Read the results set
    filename = results_filename(search_id)
    with open(filename, 'rt') as res_file:
        resultsReader = csv.DictReader(res_file)
        laws_found = list(resultsReader)
        # import pdb; pdb.set_trace()

    # Specify email headers
    subject = settings.APP_NAME + ' -- Search Results -- ' + gen_date
    sender_email = 'CFCapp@ibm.com'
    user = request.user
    recipients = [recipient_format(user.first_name,
                                   user.last_name,
                                   user.email)]

    # If the EMAIL_HOST is configured in cfc_project/settings.py
    if settings.EMAIL_HOST:
        context = {'laws_found': laws_found,
                   'gen_date': gen_date}
        text_version = render_to_string(
            template_name='email-results.txt',
            context=context, request=request)
        html_version = render_to_string(
            template_name='email-results.html',
            context=context, request=request)

        sent = send_mail(subject, text_version, sender_email, recipients,
                         fail_silently=True, html_message=html_version)

        # the variable "sent" represents the number of emails successfully
        # sent.  Thus, 0=none sent, and 1=one sent successfull
        if sent > 0:
            status_message = 'Mail successfully sent to:'
        else:
            status_message = 'ERROR: Unable to deliver email'
    else:
        status_message = 'ERROR: EMAIL_HOST environment variable not defined'

    context = {'status_message': status_message,
               'recipients': recipients,
               'search_id': search_id}
    return render(request, 'email_sent.html', context)
