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
# Debug with:  import pdb; pdb.set_trace()

import json
from django.core.management.base import BaseCommand, CommandError
from cfc_app.models import Location
from cfc_app.Legiscan_Tony import Legiscan_API
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings

StateForm = 'File {}: Session {} Year: {} Date: {} Size: {} bytes'


class Command(BaseCommand):
    help = 'For each state in the United States listed under LOCATIONS, '
    help += 'this script will fetch the most recent legislative sessions, '
    help += 'and create a json output file SS-NNNN.json where '
    help += 'SS is the two-letter state abbreviation like AZ or OH, and '
    help += 'NNNN is the four-digit session_id from Legiscan.com API.'
    help += 'The SS-NNNN.json files are stored in File/Object Storage.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = Legiscan_API()
        self.use_api = False
        self.limit = 1
        self.list_name = 'Legiscan-List.json'
        self.list_data = None
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Number of legislative sessions per state")

        return None

    def handle(self, *args, **options):

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.use_api = True
            if not self.fob.item_exists(self.list_name):
                self.list_data = self.leg.get_dataset_list(apikey='Bad')
                self.fob.upload_text(self.list_data, self.list_name)

        if not self.list_data:
            if self.fob.item_exists(self.list_name):
                self.list_data = self.fob.download_text(self.list_name)
            else:
                raise CommandError('File not found: '+self.list_name)

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)

        states = []
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            state_id = loc.legiscan_id

            states.append([state, state_id])
            if options['state']:
                if state != options['state']:
                    continue

            response = json.loads(self.list_data)

            # import pdb; pdb.set_trace()

            if 'status' in response:
                if response['status'] != 'OK':
                    raise CommandError('Status not OK: '+self.list_name)
                else:
                    if 'datasetlist' not in response:
                        raise CommandError('datsetlist missing')
                    else:
                        datasetlist = response['datasetlist']

            num = 0
            for entry in datasetlist:
                if entry['state_id'] == state_id:
                    session_id = entry['session_id']
                    access_key = entry['access_key']
                    session_name = self.json_name(state, session_id)
                    if self.use_api and self.leg.api_ok:
                        print('Fetching {}: {}'.format(state, state_id))
                        session_data = self.leg.get_session_id(session_id,
                                                               access_key,
                                                               apikey='Bad')
                        self.fob.upload_text(session_data, session_name)
                        num += 1
                        if self.limit > 0 and num >= self.limit:
                            break

        for state_data in states:
            state, state_id = state_data[0], state_data[1]
            datasetlist = json.loads(self.list_data)['datasetlist']
            num = 0
            found_list = self.fob.list_items(prefix=state, suffix='.json')
            for entry in datasetlist:
                if entry['state_id'] == state_id:
                    session_id = entry['session_id']
                    session_name = self.json_name(state, session_id)
                    if session_name in found_list:
                        self.show_results(session_name, entry)
                    else:
                        print('FILE NOT FOUND: ', session_name)
                    num += 1
                    if self.limit > 0 and num >= self.limit:
                        break

        return None

    def json_name(self, state, state_id):
        item_name = "{}-{:04d}.json".format(state, state_id)
        return item_name

    def show_results(self, json_name, entry):
        year_range = str(entry['year_start'])
        if year_range != entry['year_end']:
            year_range += '-' + str(entry['year_end'])

        print(StateForm.format(json_name, entry['session_id'],
                               year_range, entry['dataset_date'],
                               entry['dataset_size']))
        return None
