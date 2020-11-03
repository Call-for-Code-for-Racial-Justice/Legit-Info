#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Log start and stop times

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import datetime as DT
import logging
import sys

# Django and other third-party imports
import pytz

# Application imports

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

VERBOSE = 1
LOCAL_TIMEZONE = 'MST'   # Mountain Standard Time (Arizona)


class LogTime():
    """ Log time of activity """

    def __init__(self, name):
        self.name = name
        self.start = None
        self.end = None
        return None

    def start_time(self, verbosity=VERBOSE):
        """ Display start time in local time zone """

        self.start = LogTime.time_now(f"Starting {self.name}",
                                      verbosity=verbosity)
        return self.start

    def end_time(self, verbosity=VERBOSE):
        """ Display end time in local time zone """

        self.end = LogTime.time_now(f"Ending {self.name}",
                                    verbosity=verbosity)
        return self.end

    @staticmethod
    def time_now(tag, verbosity=VERBOSE):
        """ Get the time now in current time zone """

        now = DT.datetime.now(pytz.timezone(LOCAL_TIMEZONE))
        now_local = now.strftime("%b-%d %I:%M%p %Z")
        msg = f"{tag} at {now_local}"
        if verbosity > 0:
            print(msg)
        logger.info(msg)
        return now


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    test1 = LogTime('Test One')
    test1.start_time(1)

    print('Test Verbosity')
    test1.start_time(verbosity=0)
    print('End Test Verbosity')

    test1.end_time(1)


# end of module
