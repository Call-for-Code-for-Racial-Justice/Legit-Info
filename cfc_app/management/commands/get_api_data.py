# Python Code
# get_api_data.py

from django.core.management.base import BaseCommand
from cfc_app.models import Location
from cfc_app.Legiscan_API import Legiscan_API


class Command(BaseCommand):
    help = 'For each state in the United States listed under LOCATIONS, '
    help += 'this script will fetch the most recent legislative session, '
    help += 'and create a json output file under /sources/NN.json where, '
    help += 'NN is the two-letter state abbreviation like AZ or OH.  You '
    help += 'may limit to single state using --state AZ or --state OH.   '
    help += 'Omit --fresh if you do not want to invoke Legiscan API      '

    def add_arguments(self, parser):
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--fresh", action="store_true",
                            help="Invoke Legiscan.com API")
        return self

    def handle(self, *args, **options):
        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)

        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            if options['state']:
                if state != options['state']:
                    continue

            print('Fetching for state: {} -- {}'.format(state, loc.desc))
            if options['fresh']:
                leg = Legiscan_API()
                leg.getAllBills(state)
        return None
