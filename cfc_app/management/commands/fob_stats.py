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
import logging

# Django and other third-party imports
from django.core.management.base import BaseCommand

# Application imports
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.KeyCounter import KeyCounter

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

STATE_LIST = ['AZ', 'OH', 'US']


class Command(BaseCommand):
    """ Python customized command: fob_stats """

    help = 'See Location and Impact database tables. '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob_file = FOB_Storage('FILE')
        self.fob_object = FOB_Storage('OBJECT')
        self.maxlimit = 400
        self.mode = "FILE"
        self.verbosity = 1
        self.by_state = KeyCounter("By STATE")
        self.by_ext = KeyCounter("By extension")
        self.limit = 0
        return None

    def add_arguments(self, parser):
        parser.add_argument("--prefix", help="Prefix of item names")
        parser.add_argument("--suffix", help="Suffix of item names")
        parser.add_argument("--after", help="Start after this item name")
        parser.add_argument("--mode", help="From FILE, OBJECT, or BOTH")
        parser.add_argument("--limit", help="Number of items to process",
                            type=int, default=self.limit)  # 0 is UNLIMITED
        return None

    def handle(self, *args, **options):

        mode = self.mode
        if options['mode']:
            mode = options['mode']

        if options['verbosity']:
            self.verbosity = options['verbosity']

        if mode in ['FILE', 'BOTH']:
            self.fob_file = FOB_Storage('FILE')
            fob = self.fob_file
            self.show_stats(fob, 'FILE', options)

        if mode in ['OBJECT', 'BOTH']:
            self.fob_object = FOB_Storage('OBJECT')
            fob = self.fob_object
            self.show_stats(fob, 'OBJECT', options)

        self.limit = options['limit']
        return None

    def show_stats(self, fob, mode, options):
        """ Display statistics gathered above """

        item_list = fob.list_items(prefix=options['prefix'],
                                   suffix=options['suffix'],
                                   after=options['after'],
                                   limit=options['limit'])
        count = 0
        print(' ')
        for name in item_list:
            if self.verbosity == 2:
                print(name)

            state = name[:2]
            if state not in STATE_LIST:
                state = 'Other'

            self.by_state.consider_key(state)

            if '.' in name:
                parts = name.rsplit('.', 1)
                extension = '.' + parts[1]
                self.by_ext.consider_key(extension)

            count += 1
            if self.limit > 0 and count >= self.limit:
                break

        print('Mode = ', mode)

        self.by_state.key_results()
        self.by_ext.key_results()

        return None

# End of module
