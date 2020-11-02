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
        return None

    def handle(self, *args, **options):

        timing = LogTime("fob_sync")
        timing.start_time(options['verbosity'])

        new_options = options

        # If --only specified, ignore prefix/suffix/after options
        if new_options['only']:
            new_options['prefix'] = None
            new_options['suffix'] = None
            new_options['after'] = None
            logger.debug(f"80:fob_sync --only={new_options['only']} ")
        else:
            logger.debug(f"84:fob_sync --prefix {new_options['prefix']} "
                         f"--suffix {new_options['suffix']} "
                         f"--after {new_options['after']}")
        maxdel = min(options['maxdel'], self.maxlimit)
        maxput = min(options['maxput'], self.maxlimit)
        maxget = min(options['maxget'], self.maxlimit)
        logger.debug(f"--maxdel {maxdel}, --maxget {maxget} "
                     f"--maxput {maxput} ")

        # Get a list of ALL files on FOB FILE that match criteria
        self.flist = self.get_list(self.fob_file, new_options)

        # Get a list of ALL files on FOB FILE that match criteria
        self.olist = self.get_list(self.fob_object, new_options)

        fnum, onum = len(self.flist), len(self.olist)
        print('Number of files found:', fnum)
        print('Number of objects found:', onum)
        logger.debug(f"Number of files={fnum}, objects={onum}")

        del_count, put_count, get_count = 0, 0, 0

        # Delete items from IBM Cloud Object Store if not found on FILE.
        # If --maxdel and --maxget are both specified, --maxdel presides.
        if maxdel > 0:
            self.count = 0
            try:
                self.delete_items(maxdel, found_in='OBJECT', but_not_in='FILE')
            except Exception as e:
                logger.error(f"105:DELETE {e}", exc_info=True)
                raise FobSyncError

            del_count = self.count

            # Refresh list of ALL files on FOB FILE that match criteria
            self.olist = self.get_list(self.fob_object, new_options)

        # Send Files to Object
        if maxput > 0:
            self.count = 0
            try:
                self.copy_items(maxput, options, from_fob='FILE',
                                to_fob='OBJECT')
            except Exception as e:
                logger.error(f"119:PUT {e}", exc_info=True)
                raise FobSyncError

            put_count = self.count

        # Send Object to Files
        if maxget > 0:
            self.count = 0
            try:
                self.copy_items(maxget, options, from_fob='OBJECT',
                                to_fob='FILE')
            except Exception as e:
                logger.error(f"119:PUT {e}", exc_info=True)
                raise FobSyncError

            get_count = self.count

        print('Number of DELETE requests from OBJECT: ', del_count)
        print('Number of PUT requests from OBJECT:    ', put_count)
        print('Number of GET requests from OBJECT:    ', get_count)
        print(' ')

        timing.end_time(options['verbosity'])
        return None

    def delete_items(self, maxcount, found_in=None, but_not_in=None):
        """ delete items from OBJECT that do not exist in FILE """

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
                Hash.delete_if_exists(name, mode=found_in)
                logger.info(f"Removed from {found_in}: {name}")
                import pdb
                pdb.set_trace()
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

                logger.info(f"File {name} copied to {to_fob}")

            elif options['skip']:
                logger.debug(f"File {name} exists in both places, skipping")

            else:
                self.both_exist(name, read_from, write_to, from_fob, to_fob)

            if self.count >= maxcount:
                break

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
                print(f"Name {only_name} not found in FILE storage")
                my_list = []

        return my_list

    def both_exist(self, name, read_from, write_to, from_fob, to_fob):
        parts = name.rsplit('.', maxsplit=1)
        basename, extension = parts
        hash_from = Hash.find_item_name(name, from_fob)
        if hash_from is None:
            hash_from = self.source_hash(basename, extension, from_fob)
        # hash_to = Hash.find_item_name(name, to_fob)
        need_to_copy = False

        if need_to_copy:
            bindata = read_from.download_binary(name)
            write_to.upload_binary(bindata, name)
            logger.info(f'File {name} copied to {to_fob}')
            self.count += 1

        import pdb
        pdb.set_trace()
        return None

    def source_hash(basename, extension, from_fob):

        if extension == "json":
            pass
        elif extension == "zip":
            pass
        elif extension == "pdf":
            pass
        elif extension == "html":
            pass
        elif extension == "zip":
            pass
        else:
            logger.warning(f"261:Unrecognized extension .{extension}")

        return None

# end of module
