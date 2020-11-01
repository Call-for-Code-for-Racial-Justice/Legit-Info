#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Synchronize items in File/Object Storage between FILE and OBJECT mode.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging

# Django and other third-party imports
from django.core.management.base import BaseCommand, CommandError

# Application imports
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.LogTime import LogTime
from cfc_app.models import Hash

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class FobSyncError(CommandError):
    """ Errors raised in the fob_sync module """
    pass


class Command(BaseCommand):
    """ fob_sync command instance """

    help = ("Synchronize items in File/Object Storage.  You can control "
            "the direction by specifying --maxdel, --maxput and --maxget "
            "parameters.  To make OBJECT look like FILE, use --maxdel and "
            "--maxput only.  To make FILE look like OBJECT, use --maxget "
            "only.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob_file = FOB_Storage('FILE')
        self.flist = []
        self.fob_object = FOB_Storage('OBJECT')
        self.olist = []
        self.maxlimit = 5000
        self.count = 0
        return None

    def add_arguments(self, parser):
        parser.add_argument("--prefix", help="Prefix of names")
        parser.add_argument("--suffix", help="Suffix of names")
        parser.add_argument("--after", help="Start after this name")
        parser.add_argument("--only", help="Process this name only")
        parser.add_argument("--maxdel", type=int, default=0,
                            help="Number of deletes from OBJECT storage")
        parser.add_argument("--maxget", type=int, default=0,
                            help="Number of gets from OBJECT storage")
        parser.add_argument("--maxput", type=int, default=0,
                            help="Number of puts from OBJECT storage")
        parser.add_argument("--skip", action="store_true",
                            help="Skip copy if target exists already")
        parser.add_argument("--readback", action="store_true",
                            help="Read back and confirm data matches")

        return None

    def handle(self, *args, **options):

        new_options = options

        # If --only specified, ignore prefix/suffix/after options
        if new_options['only']:
            new_options['prefix'] = None
            new_options['suffix'] = None
            new_options['after'] = None

        timing = LogTime(__name__)
        timing.start_time(options['verbosity'])

        logger.debug(f"77:fob_sync: prefix={new_options['prefix']}")

        # Get a list of ALL files on FOB FILE that match criteria
        self.flist = self.get_list(self.fob_file, new_options)

        # Get a list of ALL files on FOB FILE that match criteria
        self.olist = self.get_list(self.fob_object, new_options)

        print('Number of files found:', len(self.flist))
        print('Number of objects found:', len(self.olist))

        maxdel = min(options['maxdel'], self.maxlimit)
        maxput = min(options['maxput'], self.maxlimit)
        maxget = min(options['maxget'], self.maxlimit)

        del_count, put_count, get_count = 0, 0, 0

        # Delete items from IBM Cloud Object Store if not found on FILE.
        # If --maxdel and --maxget are both specified, --maxdel presides.
        if maxdel > 0:
            self.count = 0
            self.delete_items(maxdel, found_in='OBJECT', but_not_in='FILE')
            del_count = self.count

            # Refresh list of ALL files on FOB FILE that match criteria
            self.olist = self.get_list(self.fob_object, new_options)

        # Send Files to Object
        if maxput > 0:
            self.count = 0
            self.copy_items(maxput, options, from_fob='FILE', to_fob='OBJECT')
            put_count = self.count

        # Send Object to Files
        if maxget > 0:
            self.count = 0
            self.copy_items(maxget, options, from_fob='OBJECT', to_fob='FILE')
            get_count = self.count

        print('Number of DELETE requests from OBJECT: ', del_count)
        print('Number of PUT requests from OBJECT:    ', put_count)
        print('Number of GET requests from OBJECT:    ', get_count)
        print(' ')

        timing.end_time(options['verbosity'])
        return None

    def delete_items(self, maxcount, found_in=None, but_not_in=None):
        """ delete items from OBJECT that do not exist in FILE """
        # import pdb; pdb.set_trace()

        if found_in == 'FILE' and but_not_in == 'OBJECT':
            item_list = self.flist
            other_list = self.olist
            remove_from = self.fob_file
        elif found_in == 'OBJECT' and but_not_in == 'FILE':
            item_list = self.olist
            other_list = self.flist
            remove_from = self.fob_object
        else:
            raise FobSyncError('Invalid combination of parameters')

        self.count = 0
        for name in item_list:
            if name not in other_list:
                remove_from.remove_item(name)
                print('Removed from {}: {}'.format(found_in, name))
                self.count += 1
                if self.count >= maxcount:
                    break
        return

    def copy_items(self, maxcount, options, from_fob=None, to_fob=None):
        """ copy items from_fob to_fob if target does not exist,
            or date/hash indicates copy is needed. """

        if (from_fob == 'FILE') and (to_fob == 'OBJECT'):
            item_list = self.flist
            other_list = self.olist
            read_from = self.fob_file
            write_to = self.fob_object
        elif (from_fob == 'OBJECT') and (to_fob == 'FILE'):
            item_list = self.olist
            other_list = self.flist
            read_from = self.fob_object
            write_to = self.fob_file
        else:
            raise CommandError('Invalid combination of parameters')

        self.count = 0
        for name in item_list:
            if name not in other_list:

                bindata = read_from.download_binary(name)
                write_to.upload_binary(bindata, name)
                self.count += 1

                if options['readback']:
                    bindata2 = self.fob_object.download_binary(name)
                    if bindata != bindata2:
                        raise CommandError('Put failed '+name)
                print('File ', name, 'copied to', to_fob)

                if self.count >= maxcount:
                    break

            elif options['skip']:
                print('File ', name, 'exists in both places, skipping')

            else:
                # perhaps we can compare files if both exist?
                self.both_exist(name, from_fob, to_fob)

        return None

    def get_list(self, fob, ops):
        """ Get list of items that match criteria. """

        my_list = fob.list_items(prefix=ops['prefix'], suffix=ops['suffix'],
                                 after=ops['after'], limit=0)

        only_name = ops['only']
        if only_name:
            if only_name in self.flist:
                my_list = [only_name]
            else:
                print('name {} not found in FILE'.format(only_name))
                my_list = []

        return my_list

    def both_exist(self, name, from_fob, to_fob):
        parts = name.rsplit('.', maxsplit=1)
        basename, extension = parts
        print(f"{name} base={basename} extension=.{extension}")
        import pdb; pdb.set_trace()
        return None

# end of module
