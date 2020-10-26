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

from django.core.management.base import BaseCommand
from cfc_app.FOB_Storage import FOB_Storage


class Command(BaseCommand):
    help = 'See Location and Impact database tables. '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob_file = FOB_Storage('FILE')
        self.fob_object = FOB_Storage('OBJECT')
        self.maxlimit = 400
        self.mode = "FILE"
        self.verbosity = 1
        return None

    def add_arguments(self, parser):
        parser.add_argument("--prefix", help="Prefix of item names")
        parser.add_argument("--suffix", help="Suffix of item names")
        parser.add_argument("--after", help="Start after this item name")
        parser.add_argument("--mode", help="From FILE, OBJECT, or BOTH")
        parser.add_argument("--limit", help="Number of items to process",
                            type=int, default=0)  # 0 is UNLIMITED
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
            self.show_stats(fob, 'FILE', prefix=options['prefix'],
                            suffix=options['suffix'], after=options['after'],
                            limit=options['limit'])

        if mode in ['OBJECT', 'BOTH']:
            self.fob_object = FOB_Storage('OBJECT')
            fob = self.fob_object
            self.show_stats(fob, 'OBJECT', prefix=options['prefix'],
                            suffix=options['suffix'], after=options['after'],
                            limit=options['limit'])
        return None

    def show_stats(self, fob, mode, prefix=None, suffix=None, after=None,
                   limit=10):
        cursor = ''
        if after:
            cursor = after

        by_state, state_list = {}, ['AZ', 'OH']
        by_ext, ext_list = {}, ['.html', '.pdf', '.txt']

        item_list = fob.list_items(prefix=prefix, suffix=suffix,
                                   after=cursor, limit=0)
        count = 0
        print(' ')
        for name in item_list:
            cursor = name
            if self.verbosity == 3:
                print(name)

            state = name[:2]
            if state not in state_list:
                state = 'Other'

            if state in by_state:
                by_state[state] += 1
            else:
                by_state[state] = 1

            extension = 'None'
            if '.' in name:
                parts = name.rsplit('.', 1)
                extension = '.' + parts[1]
                if extension not in ext_list:
                    ext_list.append(extension)

            if extension in by_ext:
                by_ext[extension] += 1
            else:
                by_ext[extension] = 1

            count += 1
            if limit > 0 and count >= limit:
                break

        print('Mode = ', mode)
        print('Total number of items processed: ', count)

        print('Statistics by STATE prefix: ')
        if 'Other' in by_state:
            state_list.append('Other')
        for state in state_list:
            if state in by_state:
                print(' ', state,  by_state[state])

        print('Statistics by extension suffix: ')
        if 'None' in by_ext:
            ext_list.append('None')
        for ext in ext_list:
            if ext in by_ext:
                print(' ', ext, by_ext[ext])

        return None
