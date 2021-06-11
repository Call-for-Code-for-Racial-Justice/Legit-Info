"""
Add states to Legit Info database using the Django Model ORM.

The user can provide the list of states as space delimited arguments in the command line. The following command
uses ./stage1 to add GA, MN, TX and CA to the local sqlite database:

./stage1 add_states GA MN TX CA

The code simply skips over state that are already in the system. The command fails if the user passes in no states
or a state that does not exist.

Written Upkar Lidder, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandParser
from django.core.exceptions import ObjectDoesNotExist
from cfc_app.models import Location
import json
import os
from django.conf import settings

import logging

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    us_state_abbrev = {'AL': 'Alabama', 'AK': 'Alaska', 'AS': 'American Samoa', 'AZ': 'Arizona', 'AR': 'Arkansas',
                       'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
                       'DC': 'Washington, DC', 'FL': 'Florida', 'GA': 'Georgia', 'GU': 'Guam', 'HI': 'Hawaii',
                       'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky',
                       'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
                       'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
                       'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
                       'NC': 'North Carolina', 'ND': 'North Dakota', 'MP': 'Northern Mariana Islands', 'OH': 'Ohio',
                       'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'PR': 'Puerto Rico',
                       'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
                       'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VI': 'Virgin Islands', 'VA': 'Virginia',
                       'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('states', nargs='+', type=str,
                            choices=self.us_state_abbrev.keys())

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        legiscan_file_path = os.path.join(settings.SOURCE_ROOT, 'legiscan_id.json')
        try:
            with open(legiscan_file_path) as file:
                legiscan_data = json.load(file)
        except EnvironmentError:
            logger.error(f'file not found: {legiscan_file_path}')

        # assuming USA is already set. If not, an exception will be thrown here
        usa = Location.objects.get(shortname='usa')

        for st in options['states']:
            try:
                st_db = Location.objects.get(shortname=st.lower())
            except ObjectDoesNotExist:
                st_db = None

            if st_db:
                logger.info(f'l31: {st}:{self.us_state_abbrev.get(st)} found, skipping.')
            else:
                # state not found, add it
                logger.info(f'l31: {st}:{self.us_state_abbrev.get(st)} missing. Adding now.')
                state = Location()
                state.shortname = st.lower()
                state.longname = self.us_state_abbrev.get(st) + ', USA'
                state.legiscan_id = \
                    list({k: v for k, v in legiscan_data.items() if v.get('code').lower() == st.lower()})[0]
                state.hierarchy = 'world.usa.' + st.lower()
                state.govlevel = 'state'
                state.save()
                state.parent = usa
                state.save()
        return None

# End of module
