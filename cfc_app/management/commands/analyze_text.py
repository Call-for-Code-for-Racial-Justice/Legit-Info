# Python Code
# analyze_text.py

from django.core.management.base import BaseCommand
from cfc_app.models import Location

class Command(BaseCommand):
    help = 'For each ...'

    def add_arguments(self, parser):
        parser.add_argument("--state", help="Process single state: AZ, OH")
        return self

    def handle(self, *args, **options):
        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)

        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            if options['state']:
                if state != options['state']:
                    continue

            print('Analyzing state: {} -- {}'.format(state,loc.desc))

