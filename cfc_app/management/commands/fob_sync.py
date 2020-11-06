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
from cfc_app.fob_storage import FobStorage
from cfc_app.log_time import LogTime
from cfc_app.models import Hash, delete_if_exists

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class FobSyncError(CommandError):
    """ Errors raised in the fob_sync module """
    pass


class FobStruct():
    """ Convenient structure to hold information about FOB """

    def __init__(self, fob, method):
        self.fob = fob
        self.method = method
        return None


class Command(BaseCommand):
    """ fob_sync command instance """

    help = ("Synchronize items in File/Object Storage.  You can control "
            "the direction by specifying --maxdel, --maxput and --maxget "
            "parameters.  To make OBJECT look like FILE, use --maxdel and "
            "--maxput only.  To make FILE look like OBJECT, use --maxget "
            "only.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob_file = FobStorage('FILE')
        self.flist = []
        self.fob_object = FobStorage('OBJECT')
        self.olist = []
        self.maxlimit = 5000
        self.maxdel = None
        self.maxput = None
        self.maxget = None
        self.count = 0
        self.ops = None
        return None

    def add_arguments(self, parser):
        """ add arguments """

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
        """ Handle the fob_sync command """

        timing = LogTime("fob_sync")
        timing.start_time(options['verbosity'])

        self.parse_options(options)

        # Get a list of ALL files on FOB FILE that match criteria
        self.flist = self.get_list(self.fob_file)

        # Get a list of ALL files on FOB FILE that match criteria
        self.olist = self.get_list(self.fob_object)

        fnum, onum = len(self.flist), len(self.olist)
        print('Number of files found:', fnum)
        print('Number of objects found:', onum)
        logger.debug(f"Number of files={fnum}, objects={onum}")

        del_count, put_count, get_count = 0, 0, 0

        # Delete items from IBM Cloud Object Store if not found on FILE.
        # If --maxdel and --maxget are both specified, --maxdel presides.
        if self.maxdel > 0:
            del_count = self.process_deletes()

        # Send Files to Object
        if self.maxput > 0:
            self.count = 0
            try:
                self.copy_items(self.maxput, options, from_fob='FILE',
                                to_fob='OBJECT')
            except Exception as exc:
                logger.error(f"119:PUT {exc}", exc_info=True)
                raise FobSyncError from exc

            put_count = self.count

        # Send Object to Files
        if self.maxget > 0:
            self.count = 0
            try:
                self.copy_items(self.maxget, options, from_fob='OBJECT',
                                to_fob='FILE')
            except Exception as exc:
                logger.error(f"119:PUT {exc}", exc_info=True)
                raise FobSyncError from exc

            get_count = self.count

        print('Number of DELETE requests from OBJECT: ', del_count)
        print('Number of PUT requests from OBJECT:    ', put_count)
        print('Number of GET requests from OBJECT:    ', get_count)
        print(' ')

        timing.end_time(options['verbosity'])
        return None

    def parse_options(self, options):
        """ Parse options """

        self.ops = options

        # If --only specified, ignore prefix/suffix/after options
        if self.ops['only']:
            self.ops['prefix'] = None
            self.ops['suffix'] = None
            self.ops['after'] = None
            logger.debug(f"80:fob_sync --only={self.ops['only']} ")
        else:
            logger.debug(f"84:fob_sync --prefix {self.ops['prefix']} "
                         f"--suffix {self.ops['suffix']} "
                         f"--after {self.ops['after']}")

        self.maxdel = min(options['maxdel'], self.maxlimit)
        self.maxput = min(options['maxput'], self.maxlimit)
        self.maxget = min(options['maxget'], self.maxlimit)
        logger.debug(f"--maxdel {self.maxdel}, --maxget {self.maxget} "
                     f"--maxput {self.maxput} ")

        return None

    def process_deletes(self):
        """ Process deletes from OBJECT storage """

        self.count = 0
        try:
            self.delete_items(self.maxdel, found_in='OBJECT',
                              but_not_in='FILE')
        except Exception as exc:
            logger.error(f"105:DELETE {exc}", exc_info=True)
            raise FobSyncError from exc

        # Refresh list of ALL files on FOB FILE that match criteria
        self.olist = self.get_list(self.fob_object)
        return self.count

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
            read_from = FobStruct(self.fob_file, from_fob)
            write_to = FobStruct(self.fob_object, to_fob)
        elif (from_fob == 'OBJECT') and (to_fob == 'FILE'):
            item_list = self.olist
            other_list = self.flist
            read_from = FobStruct(self.fob_object, from_fob)
            write_to = FobStruct(self.fob_file, to_fob)
        else:
            raise CommandError('Invalid combination of parameters')

        self.count = 0
        for name in item_list:
            if name not in other_list:

                bindata = read_from.fob.download_binary(name)
                write_to.fob.upload_binary(bindata, name)
                self.count += 1

                logger.info(f"File {name} copied to {to_fob}")

            elif options['skip']:
                logger.debug(f"File {name} exists in both places, skipping")

            else:
                self.both_exist(name, read_from, write_to)

            if self.count >= maxcount:
                break

        return None

    def get_list(self, fob):
        """ Get list of items that match criteria. """

        ops = self.ops
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

    def both_exist(self, name, read_from, write_to):
        """ When both FILE and OBJECT exist, decide whether to copy """

        parts = name.rsplit('.', maxsplit=1)
        basename, extension = parts
        hash_from = Hash.find_item_name(name, read_from.method)
        if hash_from is None:
            hash_from = Command.source_hash(basename, extension, read_from)
        # hash_to = Hash.find_item_name(name, to_fob)
        need_to_copy = False

        if need_to_copy:
            bindata = read_from.fob.download_binary(name)
            write_to.fob.upload_binary(bindata, name)
            logger.info(f'File {name} copied to {write_to.method}')
            self.count += 1

        return None

    @staticmethod
    def source_hash(basename, extension, read_from):
        """ Determine the hashcode of source file in copy """

        item_name = f"{basename}.{extension}"
        if extension == "json":
            pass
        elif extension == "zip":
            pass
        elif extension == "pdf":
            pass
        elif extension == "html":
            pass
        elif extension == "txt":
            read_from.fob.download_text(item_name)
        else:
            logger.warning(f"261:Unrecognized extension .{extension}")

        return None

# end of module
