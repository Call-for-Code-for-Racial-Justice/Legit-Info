# get_api_data.py
# By Tony Pearson, IBM, 2020
#
# This is intended as a background task
#
# You can invoke this in either "on demand" or as part of a "cron" job
#
# On Demand:
# [..] $ pipenv shell
# (cfc) $ ./stage1 get_api_data --api --state AZ --limit 10
#
# Cron Job:
# /home/yourname/Develop/legit-info/cron1 get_api_data --api --limit 10
#
# The Legiscan.com API only allows 30,000 fetches per 30-day period, and
# each legislation requires at least 2 fetches, so use the --limit keyword
#
# If you leave out the --api, the Legiscan.com API will not be invoked,
# this is useful to see the status of AZ.json and OH.json files.
#
#

import json
from django.core.management.base import BaseCommand
from cfc_app.models import Location
from cfc_app.Legiscan_API import Legiscan_API
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings

StateForm = 'File {}: Current Session {} laws, detail fetched for {} laws'


class Command(BaseCommand):
    help = 'For each state in the United States listed under LOCATIONS, '
    help += 'this script will fetch the most recent legislative session, '
    help += 'and create a json output file NN.json where '
    help += 'NN is the two-letter state abbreviation like AZ or OH.  '
    help += 'The NN.json files are stored in File/Object Storage.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = Legiscan_API()

        self.use_api = False
        self.limit = 10
        return None


    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=10,
                            help="Limit number of entries to detail")

        return None

    def handle(self, *args, **options):

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.use_api = True

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)

        states = []
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            states.append(state)
            if options['state']:
                if state != options['state']:
                    continue

            json_handle = '{}.json'.format(state)
            if self.use_api and self.leg.api_ok:
                print('Fetching {}: {}'.format(state, loc.desc))
                self.leg.getAllBills(state, json_handle, limit=self.limit)

        for state in states:
            json_handle = '{}.json'.format(state)
            success = self.fob.handle_exists(json_handle)
            if success:
                self.show_results(json_handle)
            else:
                print('FILE NOT FOUND: ', json_handle)

        return None

    def show_results(self, json_handle):
        json_str = self.fob.download_text(json_handle)
        bills = json.loads(json_str)
        session, detail = 0, 0
        for entry in bills:
            bill = bills[entry]
            if 'bill_number' in bill:
                session += 1
            if 'doc_id' in bill:
                detail += 1

        print(StateForm.format(json_handle, session, detail))
        return None
