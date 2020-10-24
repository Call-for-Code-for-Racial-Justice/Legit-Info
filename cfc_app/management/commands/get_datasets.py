# get_datasets.py
# By Tony Pearson, IBM, 2020
#
# This is intended as an asynchronous background task
#
# You can invoke this in either "on demand" or as part of a "cron" job
#
# On Demand:
# [..] $ pipenv shell
# (cfc) $ ./stage1 get_datasets --api --state AZ --limit 10
#
# Cron Job:
# /home/yourname/Develop/legit-info/cron1 get_datasets --api --limit 10
#
# The Legiscan.com API only allows 30,000 fetches per 30-day period, so
# we have optimized this application to minimize API calls to Legiscan.
#
# If you leave out the --api, the Legiscan.com API will not be invoked,
# this is useful to see the status of existing Dataset JSON files.
#
# Debug with:  import pdb; pdb.set_trace()

import datetime as DT
import json
from django.core.management.base import BaseCommand, CommandError
from cfc_app.models import Location, Hash
from cfc_app.LegiscanAPI import LegiscanAPI
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.views import load_default_locations
from django.conf import settings

LEGISCAN_ID = {
1: {"code": "AL", "name": "Alabama", "capital": "Montgomery"},
2: {"code": "AK", "name": "Alaska", "capital": "Juneau"},
3: {"code": "AZ", "name": "Arizona", "capital": "Phoenix"},
4: {"code": "AR", "name": "Arkansas", "capital": "Little Rock"},
5: {"code": "CA", "name": "California", "capital": "Sacramento"},
6: {"code": "CO", "name": "Colorado", "capital": "Denver"},
7: {"code": "CT", "name": "Connecticut", "capital": "Hartford"},
8: {"code": "DE", "name": "Delaware", "capital": "Dover"},
9: {"code": "FL", "name": "Florida", "capital": "Tallahassee"},
10: {"code": "GA", "name": "Georgia", "capital": "Atlanta"},
11: {"code": "HI", "name": "Hawaii", "capital": "Honolulu"},
12: {"code": "ID", "name": "Idaho", "capital": "Boise"},
13: {"code": "IL", "name": "Illinois", "capital": "Springfield"},
14: {"code": "IN", "name": "Indiana", "capital": "Indianapolis"},
15: {"code": "IA", "name": "Iowa", "capital": "Des Moines"},
16: {"code": "KS", "name": "Kansas", "capital": "Topeka"},
17: {"code": "KY", "name": "Kentucky", "capital": "Frankfort"},
18: {"code": "LA", "name": "Louisiana", "capital": "Baton Rouge"},
19: {"code": "ME", "name": "Maine", "capital": "Augusta"},
20: {"code": "MD", "name": "Maryland", "capital": "Annapolis"},
21: {"code": "MA", "name": "Massachusetts", "capital": "Boston"},
22: {"code": "MI", "name": "Michigan", "capital": "Lansing"},
23: {"code": "MN", "name": "Minnesota", "capital": "Saint Paul"},
24: {"code": "MS", "name": "Mississippi", "capital": "Jackson"},
25: {"code": "MO", "name": "Missouri", "capital": "Jefferson City"},
26: {"code": "MT", "name": "Montana", "capital": "Helena"},
27: {"code": "NE", "name": "Nebraska", "capital": "Lincoln"},
28: {"code": "NV", "name": "Nevada", "capital": "Carson City"},
29: {"code": "NH", "name": "New Hampshire", "capital": "Concord"},
30: {"code": "NJ", "name": "New Jersey", "capital": "Trenton"},
31: {"code": "NM", "name": "New Mexico", "capital": "Santa Fe"},
32: {"code": "NY", "name": "New York", "capital": "Albany"},
33: {"code": "NC", "name": "North Carolina", "capital": "Raleigh"},
34: {"code": "ND", "name": "North Dakota", "capital": "Bismarck"},
35: {"code": "OH", "name": "Ohio", "capital": "Columbus"},
36: {"code": "OK", "name": "Oklahoma", "capital": "Oklahoma City"},
37: {"code": "OR", "name": "Oregon", "capital": "Salem"},
38: {"code": "PA", "name": "Pennsylvania", "capital": "Harrisburg"},
39: {"code": "RI", "name": "Rhode Island", "capital": "Providence"},
40: {"code": "SC", "name": "South Carolina", "capital": "Columbia"},
41: {"code": "SD", "name": "South Dakota", "capital": "Pierre"},
42: {"code": "TN", "name": "Tennessee", "capital": "Nashville"},
43: {"code": "TX", "name": "Texas", "capital": "Austin"},
44: {"code": "UT", "name": "Utah", "capital": "Salt Lake City"},
45: {"code": "VT", "name": "Vermont", "capital": "Montpelier"},
46: {"code": "VA", "name": "Virginia", "capital": "Richmond"},
47: {"code": "WA", "name": "Washington", "capital": "Olympia"},
48: {"code": "WV", "name": "West Virginia", "capital": "Charleston"},
49: {"code": "WI", "name": "Wisconsin", "capital": "Madison"},
50: {"code": "WY", "name": "Wyoming", "capital": "Cheyenne"},
51: {"code": "DC", "name": "Washington D.C.", "capital": "Washington, DC"},
52: {"code": "US", "name": "US Congress", "capital": "Washington, DC"},
}

class Command(BaseCommand):

    StateForm = 'Session {} Year: {} Date: {} Size: {} bytes'
    VERSIONS = 5   # Number of weeks to keep DatasetLists from Legiscan

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
        self.leg = LegiscanAPI()
        self.use_api = False
        self.list_name = None
        self.list_data = None
        self.list_pkg = None
        self.datasetlist = None
        self.fromyear = 2018
        self.frequency = 7
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--frequency", type=int, default=7,
                            help="Days since last DatasetList request")
        return None

    def handle(self, *args, **options):

        # If the Legiscan DatasetList is recent enough, use it,
        # otherwise, call Legiscan API to fetch a new one

        if options['api']:
            self.use_api = True
        if options['state']:
            self.state = options['state']
        if options['frequency']:
            self.frequency = options['frequency']

        self.list_data = self.recent_enough()

        # Get the list of states from the Django database for "Location"

        try:
            usa = Location.objects.get(shortname='usa')
        except Location.DoesNotExist:
            load_default_locations()
            usa = Location.objects.get(shortname='usa')
        
        locations = Location.objects.filter(legiscan_id__gt=0)
        if not locations:
            load_default_locations()
            locations = Location.objects.filter(parent=usa)

        states = []
        for loc in locations:
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            states.append([state, state_id])
            if options['state']:
                if state != options['state']:
                    continue

            print('Processing: {} ({})'.format(loc.desc, state))

            # Get dataset and master files, up to the --limit set
            self.fetch_dataset(state, state_id)

        # Show status of all files we expect to have now
        self.datasets_found(states)
        return None

    def recent_enough(self):

        now = DT.datetime.today()
        week_ago = now - DT.timedelta(days=self.frequency)
        dsl_list = self.fob.DatasetList_items()

        latest_date = DT.datetime(1911, 6, 16, 16, 20)  # Long ago in history
        latest_name = None
        for name in dsl_list:
            mo = self.fob.DatasetList_search(name)
            if mo:
                filedate = DT.datetime.strptime(mo.group(1), "%Y-%m-%d")
                if filedate > latest_date:
                    latest_date = filedate
                    latest_name = name

        self.list_name = latest_name

        # If --api is set, but file is more than a week old, get the latest
        if self.use_api and latest_date < week_ago:
            today = now.strftime("%Y-%m-%d")
            self.list_name = self.fob.DatasetList_name(today)
            print('Fetching Dataset: {}'.format(self.list_name))
            self.list_data = self.leg.getDatasetList('Good')

            # If successful return from API, save this to a file
            if self.list_data:
                self.fob.upload_text(self.list_data, self.list_name)
                dsl_list.appen(self.list_name)
            else:
                print('API Failed to get DatasetList from Legiscan')

        # API failure or not called, get the item from File/Object storage
        if latest_name and (not self.list_data):
            print('Downloading: ', self.list_name)
            self.list_data = self.fob.download_text(self.list_name)

        if self.list_data:
            print('Verifying JSON contents of: ', self.list_name)
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

        if not self.list_data:
            print('DatasetList-YYYY-MM-DD.json not found')
            if not self.use_api:
                print('Did you forget the --api parameter?')
            raise CommandError('API failure, or DatasetList not Found')

        if len(dsl_list) > self.VERSIONS:
            dsl_list.sort(reverse=True)
            for name in dsl_list[self.VERSIONS:]:
                self.fob.remove_item(name)
                print('Removing: ', name)

        return

    def fetch_dataset(self, state, state_id):

        for entry in self.datasetlist:
            if entry['state_id'] == state_id:
                session_id = entry['session_id']
                access_key = entry['access_key']
                session_name = self.fob.Dataset_name(state, session_id)
                if entry['year_end'] >= self.fromyear:
                    hashcode, hashdate = '', "0000-00-00"
                    hash = self.check_hash(session_name)
                    if hash:
                        hashcode = hash.hashcode
                        hashdate = hash.generated_date
                    if (hashcode != entry['dataset_hash'] and
                            hashdate <= entry['dataset_date'] and
                            self.use_api and self.leg.api_ok):
                        print('Fetching {}: {}'.format(state, session_id))
                        session_data = self.leg.getDataset(session_id,
                                                           access_key)
                        self.fob.upload_text(session_data, session_name)
        return None

    def check_hash(self, session_name):
        hash = Hash.objects.filter(item_name=session_name,
                                   fob_method=settings.FOB_METHOD).first()
        return hash

    def datasets_found(self, states):
        for state_data in states:
            print(' ')
            state, state_id = state_data[0], state_data[1]
            found_list = self.fob.Dataset_items(state)
            for entry in self.datasetlist:
                if (entry['state_id'] == state_id
                        and entry['year_end'] >= self.fromyear):

                    session_id = entry['session_id']
                    session_name = self.fob.Dataset_name(state, session_id)
                    if session_name in found_list:
                        self.show_results(session_name, entry)
                        print('Found session dataset: ', session_name)
                        self.save_to_database(session_name, entry)
                    else:
                        print('Item not found: ', session_name)

        return None

    def save_to_database(self, session_name, entry):

        find_hash = self.check_hash(session_name)
        if find_hash is None:
            hash = Hash()
            hash.item_name = session_name
            hash.fob_method = settings.FOB_METHOD
            hash.generated_date = entry['dataset_date']
            hash.hashcode = entry['dataset_hash']
            hash.size = entry['dataset_size']
            hash.desc = entry['session_name']
            hash.save()

    def show_results(self, json_name, entry):
        year_range = str(entry['year_start'])
        if year_range != entry['year_end']:
            year_range += '-' + str(entry['year_end'])

        print(self.StateForm.format(entry['session_id'],
                                    year_range, entry['dataset_date'],
                                    entry['dataset_size']))
        return None
