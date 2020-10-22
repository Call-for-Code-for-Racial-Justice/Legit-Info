# Python code
# fob_sync.py
# By Tony Pearson, IBM, 2020
#
# This is intended as a one-time task for new database
#
# You can invoke this in either from Pipevn shell or native command line
#
# Pipenv Shell:
# [..] $ pipenv shell
# (cfc) $ ./stage1 seed_database
#
# Native Command Line:
# [..] $ ./cron1 seed_database
#
#
# Debug with:  import pdb; pdb.set_trace()

from django.core.management.base import BaseCommand, CommandError
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings


class Command(BaseCommand):
    help = 'See Location and Impact database tables. '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob_file = FOB_Storage('FILE')
        self.flist = []
        self.fob_object = FOB_Storage('OBJECT')
        self.olist = []
        self.maxlimit = 1000
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
        self.flist = self.fob_file.list_names(prefix=options['prefix'],
                                              suffix=options['suffix'],
                                              after=options['after'])
        name = options['only']
        if name:
            if name in self.flist or self.fob_file.name_exists(name):
                self.flist = [name]
            else:
                print('name {} not found in FILE'.format(name))
                self.flist = []

        self.olist = self.fob_object.list_names(prefix=options['prefix'],
                                                suffix=options['suffix'],
                                                after=options['after'])

        name = options['only']
        if name:
            if name in self.olist or self.fob_object.name_exists(name):
                self.olist = [name]
            else:
                print('Name {} not found in OBJECT'.format(name))
                self.olist = []

        print('Number of files found:', len(self.flist))
        print('Number of objects found:', len(self.olist))

        maxdel = min(options['maxput'], self.maxlimit)
        maxput = min(options['maxput'], self.maxlimit)
        maxget = min(options['maxget'], self.maxlimit)
        print(maxput, maxget)

        del_count, put_count, get_count = 0, 0, 0

        if maxdel > 0:
            self.delete_items(found_in='OBJECT', but_not_in='FILE',
                              limit=maxdel)

        # Send Files to Object
        if maxput > 0:
            for name in flist:
                if name not in olist:

                    bindata = self.fob_file.download_binary(name)
                    self.fob_object.upload_binary(bindata, name)
                    put_count += 1

                    if options['readback']:
                        bindata2 = self.fob_object.download_binary(name)
                        print('Length of file;', len(bindata), len(bindata2))
                        if bindata != bindata2:
                            raise CommandError('Put failed '+name)
                    print('File ', name, 'copied to OBJECT storage')

                    if put_count >= maxput:
                        break

                elif options['skip']:
                    print('File ', name, 'exists in both places, skipping')

        # Send Object to Files
        if maxget > 0:
            for name in olist:
                if name not in flist:
                    get_count += 1
                    if get_count >= maxget:
                        break
                    bindata = self.fob_object.download_binary(name)
                    self.fob_file.upload_binary(bindata, name)

                    if options['readback']:
                        bindata2 = self.fob_file.download_binary(name)
                        print('Length of file;', len(bindata), len(bindata2))
                        if bindata != bindata2:
                            raise CommandError('Put failed '+name)
                    print('Object ', name, 'copied to FILE storage')

                elif options['skip']:
                    print('Object ', name, 'exists in both places, skipping')

        print('Number of DELETE requests from OBJECT storage: ', put_count)
        print('Number of PUT requests to OBJECT storage:      ', put_count)
        print('Number of GET requests from OBJECT storage:    ', get_count)

        return None

    def del_items(self, found_in=None, but_not_in=None, limit=10):
        if found_in == 'FILE' and but_not_in == 'OBJECT':
            item_list = self.flist
            check_against = self.fob_object
            remove_from = self.fob_file
        elif found_in == 'OBJECT' and but_not_in == 'FILE':
            item_list = self.olist
            check_against = self.fob_file
            remove_from = self.fob_object
        else:
            print('Invalid combination of parameters')
            return

        count = 0
        for name in item_list:
            if not check_against.item_exists(name):
                remove_from.remove_item(name)
        return None

    def copy_names(from_fob=None, to_fob=None):
        return None
