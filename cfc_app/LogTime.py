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
# Application imports
# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

VERBOSE = 1


class LogTime():
    """ Log time of activity """

    def __init__(self, name):
        self.name = name
        return None

    def start_time(self, verbosity=VERBOSE):
        self.start = LogTime.time_now(f"Starting {self.name}",
                                      verbosity=verbosity)
        return self.start

    def stop_time(self, verbosity=VERBOSE):
        self.end = LogTime.time_now(f"Ending {self.name}",
                                    verbosity=verbosity)
        return self.end

    def time_now(tag, verbosity=VERBOSE):
        now = DT.datetime.today()
        now_local = now.strftime("%Y-%m-%d %I:%M:%S %p %Z")
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

    test1.stop_time(1)


# end of module
