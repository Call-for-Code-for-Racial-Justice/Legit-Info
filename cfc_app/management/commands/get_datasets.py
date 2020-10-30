#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Get datasetlist, and datasets for selected sessions, from Legiscan.com API.

This is phase 1 of weekly cron job.  See CRON.md for details.
Invoke with ./stage1 get_datasets  or ./cron1 get_datasets
Specify --help for details on parameters available.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import datetime as DT
import json
import logging

# Django and other third-party imports
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Application imports
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.LegiscanAPI import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.models import Location, Hash

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class GetDatasetError(CommandError):
    pass


class Command(BaseCommand):
    """ Get datasetlist, and datasets for selected sessions """

    StateForm = 'Session {} Year: {} Date: {} Size: {} bytes'
    VERSIONS = 5   # Number of weeks to keep DatasetLists from Legiscan

    help = ("Fetches DatasetList-YYYY-MM-DD.json from Legiscan.com, then "
            "for each location listed in cfc_app_law database table with "
            "a valid Legiscan_id, this script will fetch the most recent "
            "legislative sessions, and create a JSON-formatted output file "
            "CC-Dataset-NNNN.json where 'CC' is the Legiscan location code "
            "like AZ or OH, and 'NNNN' is the four-digit session_id assigned "
            "by Legiscan.com API. The DatasetList and Dataset files are "
            "stored in File/Object Storage.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = LegiscanAPI()
        self.use_api = False
        self.list_name = None
        self.list_data = None
        self.list_pkg = None
        self.datasetlist = None
        self.now = DT.datetime.today().date()
        self.fromyear = self.now.year - 2  # Back three years 2018, 2019, 2020
        self.frequency = 7
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--frequency", type=int, default=self.frequency,
                            help="Days since last DatasetList request")
        return None

    def handle(self, *args, **options):

        # If the Legiscan DatasetList is recent enough, use it,
        # otherwise, call Legiscan API to fetch a new one
        starting = '====STARTING: get_datasets'
        if options['api']:
            self.use_api = True
            starting += ' --api'
        if options['state']:
            self.state = options['state']
            starting += ' --state '+self.state
        self.frequency = options['frequency']
        starting = "{} --frequency {}".format(starting, self.frequency)
        logger.info(starting)

        self.list_data = self.recent_enough()

        # Get the list of states from the Django database for "Location"

        try:
            Location.objects.get(shortname='usa')
        except Location.DoesNotExist:
            Location.loads()

        locations = Location.objects.filter(legiscan_id__gt=0)
        if not locations:
            Location.load_defaults()
            locations = Location.objects.filter(legiscan_id__gt=0)

        states = []
        for loc in locations:
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            states.append([state, state_id])
            if options['state']:
                if state != options['state']:
                    continue

            logger.info('Processing: {} ({})'.format(loc.desc, state))

            # Get dataset and master files, up to the --limit set

            try:
                self.fetch_dataset(state, state_id)
            except Exception as e:
                err_msg = "117:Fetch Error {}".format(error)
                logger.error(err_msg, exc_info=True)           
                raise GetDatasetError

        # Show status of all files we expect to have now
        self.datasets_found(states)
        return None

    def recent_enough(self):

        week_ago = self.now - DT.timedelta(days=self.frequency)
        dsl_list = self.fob.DatasetList_items()

        latest_date = settings.LONG_AGO  # Long ago in history
        latest_name = None
        for name in dsl_list:
            mo = self.fob.DatasetList_search(name)
            if mo:
                filedate = self.date_type(mo.group(1))
                if filedate > latest_date:
                    latest_date = filedate
                    latest_name = name

        self.list_name = latest_name

        # If --api is set, but file is more than a week old, get the latest
        if self.use_api and latest_date < week_ago:
            today = self.now.strftime("%Y-%m-%d")
            self.list_name = self.fob.DatasetList_name(today)
            logger.info('Fetching Dataset: {}'.format(self.list_name))
            self.list_data = self.leg.getDatasetList('Good')

            # If successful return from API, save this to a file
            if self.list_data:
                self.fob.upload_text(self.list_data, self.list_name)
                if self.list_name not in dsl_list:
                    dsl_list.append(self.list_name)
            else:
                logger.error('API Failed to get DatasetList from Legiscan')

        # API failure or not called, get the item from File/Object storage
        if latest_name and (not self.list_data):
            logger.debug('Downloading: ' + self.list_name)
            self.list_data = self.fob.download_text(self.list_name)

        if self.list_data:
            logger.debug('Verifying JSON contents of: ' + self.list_name)
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
            logger.error('DatasetList-YYYY-MM-DD.json not found')
            if not self.use_api:
                print('Did you forget the --api parameter?')
            raise CommandError('API failure, or DatasetList not Found')

        # Let's keep only five versions of DatasetList, older ones
        # will be expired

        if len(dsl_list) > self.VERSIONS:
            dsl_list.sort(reverse=True)
            for name in dsl_list[self.VERSIONS:]:
                self.fob.remove_item(name)
                logger.debug('Expiring: ', name)

        return

    def fetch_dataset(self, state, state_id):

        for entry in self.datasetlist:
            if entry['state_id'] == state_id:
                session_id = entry['session_id']
                access_key = entry['access_key']
                session_name = self.fob.Dataset_name(state, session_id)
                if entry['year_end'] >= self.fromyear:

                    fetch_new = False
                    if self.fob.item_exists(session_name):
                        fetch_new = True

                    else:
                        entry_date = self.date_type(entry['dataset_date'])
                        hashcode, hashdate = '', settings.LONG_AGO
                        hash = Hash.find_item_name(session_name)
                        if hash:
                            hashcode = hash.hashcode
                            hashdate = hash.generated_date
                        if (hashcode != entry['dataset_hash']
                                and hashdate <= entry_date):
                            fetch_new = True

                    if fetch_new and self.use_api and self.leg.api_ok:
                        logger.info('Fetching {}: {}'.format(
                            state, session_id))

                        session_data = self.leg.getDataset(session_id,
                                                           access_key)
                        if session_data:
                            if session_data.startswith('*ERROR*'):
                                logger.error(session_data)
                            else:
                                self.fob.upload_text(session_data,
                                                     session_name)
                        else:
                            err_msg = 'Fetch unsuccessful for: '+session_name
                            raise LegiscanError(err_msg)

        return None

    def check_hash(self, session_name):
        """ Read the hash entry from Django cfc_app_hash database table """
        hash = Hash.objects.filter(item_name=session_name,
                                   fob_method=settings.FOB_METHOD).first()
        return hash

    def date_type(self, date_string):
        """ Convert "YYYY-MM-DD" string to datetime.date format """
        date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
        return date_value

    def datasets_found(self, states):
        for state_data in states:

            state, state_id = state_data[0], state_data[1]
            found_list = self.fob.Dataset_items(state)
            for entry in self.datasetlist:
                if (entry['state_id'] == state_id
                        and entry['year_end'] >= self.fromyear):

                    session_id = entry['session_id']
                    session_name = self.fob.Dataset_name(state, session_id)
                    if session_name in found_list:
                        self.show_results(session_name, entry)
                        print('Found session dataset: '+session_name)
                        self.save_to_database(session_name, entry)
                    else:
                        print('Item not found: '+session_name)

        return None

    def save_to_database(self, session_name, entry):

        find_hash = Hash.find_item_name(session_name)
        if find_hash is None:
            hash = Hash()
            hash.item_name = session_name
            hash.fob_method = settings.FOB_METHOD
            hash.desc = entry['session_name']
            hash.generated_date = entry['dataset_date']
            hash.hashcode = entry['dataset_hash']
            hash.size = entry['dataset_size']
            hash.save()

        else:
            find_hash.generated_date = entry['dataset_date']
            find_hash.hashcode = entry['dataset_hash']
            find_hash.size = entry['dataset_size']
            find_hash.save()

        return None

    def show_results(self, json_name, entry):
        year_range = str(entry['year_start'])
        if year_range != entry['year_end']:
            year_range += '-' + str(entry['year_end'])

        logger.info(self.StateForm.format(entry['session_id'],
                                          year_range, entry['dataset_date'],
                                          entry['dataset_size']))
        return None
