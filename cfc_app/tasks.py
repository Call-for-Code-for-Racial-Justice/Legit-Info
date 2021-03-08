#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/tasks.py -- Asynchronous tasks for Django-Q scheduler

Written by Tony Pearson, IBM, 2021
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import os
import logging
from datetime import datetime
from contextlib import redirect_stdout
import sys

# Django and other third-party imports
from django.core.management import call_command
from django.conf import settings


# Application imports
from .management.commands import get_datasets



# Debugging options
# return HttpResponse({variable to inspect})
# logger.debug {variable to inspect}
# raise Exception({variable to inspect})
# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

#########################
# Support functions here
#########################

def gen_output_name(cmd):
    today = datetime.now()
    gen_date = today.strftime("%Y-%m-%d")
    logname = f"{cmd}_{gen_date}.msg"
    logpath = os.path.join(settings.MEDIA_ROOT, logname)
    return logpath

#########################
# Create your views here.
#########################

def cron_step1_get_datasets(*args, **kwargs):
    logger.info(f"51:task started: cron_step1_get_datasets")

    outfile = gen_output_name('get_datasets')
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command('get_datasets', '--api')

    logger.info(f"52:task ended: cron_step1_get_datasets")
    return

def cron_step2_extract_files(*args, **kwargs):
    logger.info(f"57:task started: cron_step2_extract_files")

    outfile = gen_output_name('extract_files')
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command('extract_files', '--api', '--skip', '--limit 10')

    logger.info(f"58:task ended: cron_step2_extract_files")
    return

def cron_step3_analyze_text():
    logger.info(f"62:task started: cron_step3_analyze_text")

    outfile = gen_output_name('analyze_text')
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command('analyze_text', '--api', '--skip', '--compare',
                         '--limit 10')

    logger.info(f"63:task ended: cron_step3_analyze_text")
    return

def fob_stats():
    logger.info(f"66:task started: fob_stats")
    logger.info(f"67:task ended: fob_stats")
    return

def fob_sync():
    logger.info(f"71:task started: fob_sync")
    logger.info(f"72:task ended: fob_sync")
    return



