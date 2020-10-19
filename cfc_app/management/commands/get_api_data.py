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
from cfc_app.Legiscan_API import Legiscan_API
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings

StateForm = 'File {}: Session {} Year: {} Date: {} Size: {} bytes'


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
        self.limit = 1
        self.list_handle = 'Legiscan-List.json'
        self.list_data = None
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Limit number of entries per state")

        return None

    def handle(self, *args, **options):

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.use_api = True
            if not self.fob.handle_exists(self.list_handle):
                self.list_data = self.leg.get_dataset_list()
                self.fob.upload_text(self.list_data, self.list_handle)

        if not self.list_data:
            if self.fob.handle_exists(self.list_handle):
                self.list_data = self.fob.download_text(self.list_handle)
            else:
                raise CommandError('File not found: '+self.list_handle)

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
                    raise CommandError('Status not OK: '+self.list_handle)
                else:
                    if 'datasetlist' not in response:
                        raise CommandError('datsetlist missing')
                    else:
                        datasetlist = response['datasetlist']

            num = 0
            for entry in datasetlist:
                if entry['state_id'] == state_id:
                    session_id = entry['session_id']
                    session_handle = self.json_handle(state, session_id)
                    if self.use_api and self.leg.api_ok:
                        print('Fetching {}: {}'.format(state, state_id))
                        session_data = self.leg.get_session_id(session_id)
                        self.fob.upload_text(session_data, session_handle)
                        num += 1
                        if self.limit > 0 and num >= self.limit:
                            break

        for state_data in states:
            state, state_id = state_data[0], state_data[1]
            datasetlist = json.loads(self.list_data)['datasetlist']
            num = 0
            found_list = self.fob.list_handles(prefix=state, suffix='.json')
            for entry in datasetlist:
                if entry['state_id'] == state_id:
                    session_id = entry['session_id']
                    session_handle = self.json_handle(state, session_id)
                    if session_handle in found_list:
                        self.show_results(session_handle, entry)
                    else:
                        print('FILE NOT FOUND: ', session_handle)
                    num += 1
                    if self.limit > 0 and num >= self.limit:
                        break

        return None

    def json_handle(self, state, state_id):
        handle = "{}-{:04d}.json".format(state, state_id)
        return handle

    def show_results(self, json_handle, entry):
        year_range = str(entry['year_start'])
        if year_range != entry['year_end']:
            year_range += '-' + str(entry['year_end'])

        print(StateForm.format(json_handle, entry['session_id'],
                               year_range, entry['dataset_date'],
                               entry['dataset_size']))
        return None
