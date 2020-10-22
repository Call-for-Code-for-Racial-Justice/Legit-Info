# get_api_data.py
# By Tony Pearson, IBM, 2020
#
# This is intended as an asynchronous background task
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
    help = ("For each state in the United States listed in cfc_app_law "
            "database table, this script will fetch the most recent "
            "legislative sessions, and create a JSON-formatted output file "
            "SS-NNNN.json where 'SS' is the two-letter state abbreviation "
            "like AZ or OH, and 'NNNN' is the four-digit session_id assigned "
            "by Legiscan.com API. The SS-NNNN.json files are stored in "
            "File/Object Storage.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = Legiscan_API()
        self.use_api = False
        self.limit = 1
        self.list_name = 'Legiscan-List.json'
        self.list_data = None
        self.list_pkg = None
        self.datasetlist = None
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

        # If --api use requested, call Legiscan for Legiscan-List.json
        # Otherwise, read the one we have already

        if options['api']:
            self.use_api = True
            self.list_data = self.leg.getDatasetList('Good')
            if self.list_data:
                self.fob.upload_text(self.list_data, self.list_name)

        if self.list_data is None:
            if self.fob.item_exists(self.list_name):
                self.list_data = self.fob.download_text(self.list_name)

        if self.list_data is None:
            raise CommandError('File not found: '+self.list_name)

        self.list_pkg = json.loads(self.list_data)

        # Validate this is a Legiscan DatasetList file
        if 'status' in self.list_pkg:
            if self.list_pkg['status'] != 'OK':
                raise CommandError('Status not OK: '+self.list_name)
            else:
                if 'datasetlist' not in self.list_pkg:
                    raise CommandError('datsetlist missing')
                else:
                    self.datasetlist = self.list_pkg['datasetlist']

        # Get the list of states from the Django database for "Location"

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

            # import pdb; pdb.set_trace()

            # Get dataset and master files, up to the --limit set
            self.fetch_dataset_master(state, state_id)

        # Show status of all files we expect to have now
        self.datasets_found(states)
        return None

    def dsl_name(self, state, state_id):
        item_name = "{}-{:04d}-Dataset.json".format(state, state_id)
        return item_name

    def mast_name(self, state, state_id):
        item_name = "{}-{:04d}-Master.json".format(state, state_id)
        return item_name

    def fetch_dataset_master(self, state, state_id):
        num = 0
        for entry in self.datasetlist:
            if entry['state_id'] == state_id:
                session_id = entry['session_id']
                access_key = entry['access_key']
                session_name = self.dsl_name(state, session_id)
                master_name = self.mast_name(state, session_id)
                if self.use_api and self.leg.api_ok:
                    print('Fetching {}: {}'.format(state, session_id))
                    session_data = self.leg.getDataset(session_id,
                                                       access_key)
                    self.fob.upload_text(session_data, session_name)

                    master_data = self.leg.getMasterList(session_id)
                    self.fob.upload_text(master_data, master_name)

                    num += 1
                    if self.limit > 0 and num >= self.limit:
                        break

    def datasets_found(self, states):
        for state_data in states:
            state, state_id = state_data[0], state_data[1]
            datasetlist = json.loads(self.list_data)['datasetlist']
            num = 0
            found_list = self.fob.list_items(prefix=state, suffix='.json')
            for entry in datasetlist:
                if entry['state_id'] == state_id:
                    session_id = entry['session_id']
                    session_name = self.dsl_name(state, session_id)
                    if session_name in found_list:
                        self.show_results(session_name, entry)
                    else:
                        print('FILE NOT FOUND: ', session_name)

                    master_name = self.mast_name(state, session_id)
                    if master_name in found_list:
                        print('Found Master List: ', master_name)
                    else:
                        print('FILE NOT FOUND: ', master_name)

                    num += 1
                    if self.limit > 0 and num >= self.limit:
                        break
        return None

    def show_results(self, json_name, entry):
        year_range = str(entry['year_start'])
        if year_range != entry['year_end']:
            year_range += '-' + str(entry['year_end'])

        print(StateForm.format(json_name, entry['session_id'],
                               year_range, entry['dataset_date'],
                               entry['dataset_size']))
        return None
