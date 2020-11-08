#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper functions for File/Object Storage

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging
import re

# Django and other third-party imports

# Application imports
from cfc_app.fob_storage import FobStorage

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

MAXLIMIT = 1000
DSLregex = re.compile(r'^DatasetList-(\d\d\d\d-\d\d-\d\d).json$')
DSNregex = re.compile(r'^([A-Z]{2})-Dataset-(\d\d\d\d).json$')
BTregex = re.compile(r'^([A-Z]{2})-([A-Z0-9]*)-(\d\d\d\d)(.json|.pdf|.html)$')

BN_REGEX = re.compile("([A-Z]*)([0-9]*)")


class FobHelper():
    """ Support both Local File and Remote Object Storage """

    def __init__(self, fob):
        self.fob = fob
        return None

    # Helpers for Legiscan DatasetList (DatasetList-YYYY-MM-DD.json)
    def datasetlist_items(self):
        """ Get all items that are datasetlists """

        dsl_list = self.fob.list_items(prefix='DatasetList-', suffix='.json')
        return dsl_list

    @staticmethod
    def datasetlist_search(item_name):
        """ Return REGEX search value of item """

        mop = DSLregex.search(item_name)
        return mop

    @staticmethod
    def datasetlist_name(today):
        """ Generate name for Legiscan DatasetList """

        return 'DatasetList-{}.json'.format(today)

    # Helpers for Legiscan Dataset (SS-Dataset-NNNN.json)
    def dataset_items(self, state):
        """ Get all items that are datasets """

        dsn_prefix = "{}-Dataset-".format(state)
        dsl_list = self.fob.list_items(prefix=dsn_prefix, suffix='.json')
        return dsl_list

    @staticmethod
    def dataset_search(item_name):
        """ Return REGEX search value of item """

        mop = DSNregex.search(item_name)
        return mop

    @staticmethod
    def dataset_name(state, state_id):
        """ generate valid dataset filename """

        item_name = "{}-Dataset-{:04d}.json".format(state, state_id)
        return item_name

    # Helpers for Legiscan BillText (CC-BODY-SSSS-YNNNN.json)
    def bill_text_items(self, state, extension):
        """ Get all items that are individual laws (PDF/HTML/TXT) """

        dsn_prefix = "{}-".format(state)
        dsl_list = self.fob.list_items(prefix=dsn_prefix, suffix=extension)
        return dsl_list

    @staticmethod
    def bill_text_search(item_name):
        """ Return REGEX search value of item """

        mop = BTregex.search(item_name)
        return mop

    @staticmethod
    def bill_text_key(state, bill_number, session_id, doc_year):
        """ Generate key in correct format """

        mop = BN_REGEX.search(bill_number)
        bill_no = bill_number
        if mop:
            body = mop.group(1)
            bnum = mop.group(2)
            if len(bnum) < 4:
                bill_no = "{}{:0>4}".format(body, bnum)

        key = "{}-{}-{}".format(state, bill_no, session_id)
        if len(key) <= 19:
            key += "-Y" + str(doc_year)
        elif len(key) <= 21:
            key += "-Y" + str(doc_year)[2:4]
        return key

    @staticmethod
    def bill_text_name(key, extension):
        """ Generate filename for legislation in correct format """

        ext = extension.lower()
        item_name = "{}.{}".format(key, ext)
        return item_name


if __name__ == "__main__":

    fob = FobStorage('FILE', filesys='/tmp/FOB-TEST', bucket='fob-test')
    helper = FobHelper(fob)
    if helper:
        print(helper)

    print('Congratulations')
