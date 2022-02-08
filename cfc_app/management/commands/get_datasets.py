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
from cfc_app.fob_storage import FobStorage
from cfc_app.fob_helper import FobHelper
from cfc_app.legiscan_api import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.log_time import LogTime
from cfc_app.models import Location, Hash, save_entry_to_hash
from cfc_app.bill_detail import date_type


# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

###########################################
# Support functions
###########################################


def show_results(entry):
    """ Show results / existence of files """

    year_range = str(entry['year_start'])
    if year_range != entry['year_end']:
        year_range += '-' + str(entry['year_end'])

    logger.info(f"Session {entry['session_id']} Year: {year_range} "
                f"Date: {entry['dataset_date']} "
                f"Size: {entry['dataset_size']} bytes")
    return None


class GetDatasetError(CommandError):
    """ Customized error class for this command """
    pass


class Command(BaseCommand):
    """ Get datasetlist, and datasets for selected sessions """

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
        self.fob = FobStorage(settings.FOB_METHOD)
        self.fobhelp = FobHelper(self.fob)
        self.leg = LegiscanAPI()
        self.use_api = False
        self.list_name = None
        self.list_data = None
        self.list_pkg = None
        self.datasetlist = None
        self.dsl_list = None
        self.now = DT.datetime.today().date()
        self.latest_date = None
        self.latest_name = None
        self.fromyear = self.now.year - 2  # Back three years 2018, 2019, 2020
        self.frequency = 7
        self.state = None
        return None

    def add_arguments(self, parser):
        """ add parser arguments for this command """

        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--frequency", type=int, default=self.frequency,
                            help="Days since last DatasetList request")
        return None

    def handle(self, *args, **options):
        """ Handle main logic of this command """

        # If the Legiscan DatasetList is recent enough, use it,
        # otherwise, call Legiscan API to fetch a new one
        timing = LogTime("get_datasets")
        timing.start_time(options['verbosity'])

        if options['api']:
            self.use_api = True
        if options['state']:
            self.state = options['state']
        self.frequency = options['frequency']
        logger.debug(f"115:Options {options}")

        self.recent_enough()

        # Get the list of states from the Django database for "Location"

        try:
            Location.objects.get(shortname='usa')
        except Location.DoesNotExist:
            Location.load_defaults()

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

            logger.info(f"Processing: {loc.longname} ({state})")

            # Get dataset and master files, up to the --limit set

            try:
                self.fetch_dataset(state, state_id)
            except Exception as exc:
                logger.error(f"149:Fetch Error {exc}", exc_info=True)
                raise GetDatasetError from exc

        # Show status of all files we expect to have now
        self.datasets_found(states)

        timing.end_time(options['verbosity'])
        return None

    def recent_enough(self):
        """ Check of datasetlist is recent enough to use 'as is' """

        week_ago = self.now - DT.timedelta(days=self.frequency)
        self.dsl_list = self.fobhelp.datasetlist_items()
        logger.debug(f"163:DSL List: [{self.dsl_list}]")
        self.find_latest_dsl()

        # If --api is set, but file is more than a week old, get the latest
        if self.use_api and self.latest_date <= week_ago:
            self.fetch_dsl_api()

        # API failure or not called, get the item from File/Object storage
        if self.latest_name and (not self.list_data):
            logger.debug(f"172:Downloading: [{self.list_name}]")
            self.list_name = self.latest_name
            self.list_data = self.fob.download_text(self.list_name)

        if self.list_data:
            logger.debug(f"177:Verifying JSON contents of: {self.list_name}")
            self.list_pkg = json.loads(self.list_data)

            # Validate this is a Legiscan DatasetList file
            if 'status' in self.list_pkg:
                if ((self.list_pkg['status'] == 'OK')
                        and ('datasetlist' in self.list_pkg)):
                    self.datasetlist = self.list_pkg['datasetlist']
                else:
                    raise CommandError(f"Status not OK: {self.list_name}")

        if not self.list_data:
            logger.error('180:DatasetList-YYYY-MM-DD.json not found')
            if not self.use_api:
                self.stdout.write(self.style.WARNING(
                    'Did you forget the --api parameter?'))
            raise CommandError('API failure, or DatasetList not Found')

        # Let's keep only five versions of DatasetList, older ones
        # will be expired

        if len(self.dsl_list) > self.VERSIONS:
            self.dsl_list.sort(reverse=True)
            for name in self.dsl_list[self.VERSIONS:]:
                self.fob.remove_item(name)
                logger.debug(f"201:Expiring: {name}")

        return

    def find_latest_dsl(self):
        """ Find the most recent DatasetList obtained from Legiscan """

        self.latest_date = settings.LONG_AGO  # Long ago in history
        self.latest_name = None
        for name in self.dsl_list:
            mop = self.fobhelp.datasetlist_search(name)
            if mop:
                filedate = date_type(mop.group(1))
                if filedate > self.latest_date:
                    self.latest_date = filedate
                    self.latest_name = name

        return None

    def fetch_dsl_api(self):
        """ Fetch datasetlist from Legiscan API """

        today = self.now.strftime("%Y-%m-%d")
        self.list_name = self.fobhelp.datasetlist_name(today)
        logger.info(f"Fetching Dataset: {self.list_name}")

        self.list_data = self.leg.get_datasetlist('Good')
        # If successful return from API, save this to a file
        if self.list_data:
            self.fob.upload_text(self.list_data, self.list_name)
            if self.list_name not in self.dsl_list:
                self.dsl_list.append(self.list_name)
        else:
            logger.error('API Failed to get DatasetList from Legiscan')

        return None

    def fetch_dataset(self, state, state_id):
        """ Fetch dataset for specific legislative session """

        for entry in self.datasetlist:
            if entry['state_id'] == state_id:
                session_id = entry['session_id']
                session_name = self.fobhelp.dataset_name(state, session_id)
                if entry['year_end'] >= self.fromyear:
                    self.fetch_from_api(session_name, entry)

        return None

    def fetch_from_api(self, session_name, entry):
        """ Fetch dataset from Legiscan API """

        fetch_new = False
        if self.fob.item_exists(session_name):
            entry_date = date_type(entry['dataset_date'])
            hashcode, hashdate = '', settings.LONG_AGO
            ds_hash = Hash.find_item_name(session_name)
            if ds_hash:
                hashcode = ds_hash.hashcode
                hashdate = ds_hash.generated_date
            if (hashcode != entry['dataset_hash']
                    and hashdate <= entry_date):
                fetch_new = True
        else:
            fetch_new = True

        if fetch_new and self.use_api and self.leg.api_ok:
            logger.info(f"Fetching {session_name}")
            session_id = entry['session_id']
            access_key = entry['access_key']
            session_data = self.leg.get_dataset(session_id, access_key)
            if session_data:
                if session_data.startswith('*ERROR*'):
                    logger.error(f"228:{session_data}")
                else:
                    self.fob.upload_text(session_data, session_name)
            else:
                err_msg = 'Fetch unsuccessful for: '+session_name
                raise LegiscanError(f"234:{err_msg}")

        return None

    def datasets_found(self, states):
        """ Process datasets found """

        for state_data in states:

            state, state_id = state_data[0], state_data[1]
            found_list = self.fobhelp.dataset_items(state)
            for entry in self.datasetlist:
                if (entry['state_id'] == state_id
                        and entry['year_end'] >= self.fromyear):

                    session_id = entry['session_id']
                    session_name = self.fobhelp.dataset_name(state, session_id)
                    if session_name in found_list:
                        show_results(entry)
                        self.stdout.write(self.style.SUCCESS(
                            'Found session dataset: '+session_name))
                        save_entry_to_hash(session_name, entry)
                    else:
                        self.stdout.write(self.style.WARNING(
                            'Item not found: '+session_name))

        return None

# end of module
