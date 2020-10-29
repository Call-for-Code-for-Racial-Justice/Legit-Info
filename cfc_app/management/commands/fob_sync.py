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


class Command(BaseCommand):
    help = 'See Location and Impact database tables. '

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

        prefix = options['prefix']
        suffix = options['suffix']
        after = options['after']

        # If --only specified, ignore prefix/suffix/after options
        only_name = None
        if options['only']:
            only_name = options['only']
            prefix = None
            suffix = None
            after = None

        # Get a list of ALL files on FOB FILE that match criteria
        self.flist = self.get_list(self.fob_file, prefix, suffix,
                                   after, only_name)

        # Get a list of ALL files on FOB FILE that match criteria
        self.olist = self.get_list(self.fob_object, prefix, suffix,
                                   after, only_name)

        print('Number of files found:', len(self.flist))
        print('Number of objects found:', len(self.olist))

        maxdel = min(options['maxdel'], self.maxlimit)
        maxput = min(options['maxput'], self.maxlimit)
        maxget = min(options['maxget'], self.maxlimit)

        del_count, put_count, get_count = 0, 0, 0

        # Delete items from IBM Cloud Object Store if not found on FILE
        if maxdel > 0:
            self.count = 0
            self.delete_items(maxdel, found_in='OBJECT', but_not_in='FILE')
            del_count = self.count

            # Refresh list of ALL files on FOB FILE that match criteria
            self.olist = self.get_list(self.fob_object, prefix, suffix,
                                       after, only_name)

        # Send Files to Object
        if maxput > 0:
            self.count = 0
            self.copy_items(maxput, options, from_fob='FILE', to_fob='OBJECT')
            put_count = self.count

        # Send Object to Files
        if maxget > 0:
            self.count = 0
            self.get_count = self.copy_items(maxget, options,
                                             from_fob='OBJECT', to_fob='FILE')
            get_count = self.count

        print('Nunmber of DELETE requests from OBJECT: ', del_count)
        print('Nunmber of PUT requests from OBJECT:    ', put_count)
        print('Nunmber of GET requests from OBJECT:    ', get_count)
        return None

    def delete_items(self, maxcount, found_in=None, but_not_in=None):
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
            raise CommandError('Invalid combination of parameters')

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
                pass

        return None

    def get_list(self, fob, prefix, suffix, after, only_name):
        my_list = fob.list_items(prefix=prefix, suffix=suffix,
                                 after=after, limit=0)
        if only_name:
            if only_name in self.flist:
                my_list = [only_name]
            else:
                print('name {} not found in FILE'.format(only_name))
                my_list = []
        return my_list
