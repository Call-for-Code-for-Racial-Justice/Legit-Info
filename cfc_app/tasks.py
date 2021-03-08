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

# Django and other third-party imports
from django.core.management import call_command
from django.conf import settings


# Application imports


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
    logger.info("51:task started: cron_step1_get_datasets")

    cmd = 'get_datasets'
    logpath = gen_output_name(cmd)
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command(cmd, '--api')

    logger.info("58:task ended: cron_step1_get_datasets")
    return


def cron_step2_extract_files(*args, **kwargs):
    logger.info("63:task started: cron_step2_extract_files")

    cmd = 'extract_files'
    logpath = gen_output_name(cmd)
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command(cmd, '--api', '--skip', '--limit 10')

    logger.info("71:task ended: cron_step2_extract_files")
    return


def cron_step3_analyze_text():
    logger.info("76:task started: cron_step3_analyze_text")

    cmd = 'analyze_text'
    logpath = gen_output_name(cmd)
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command(cmd, '--api', '--skip', '--compare', '--limit 10')

    logger.info("84:task ended: cron_step3_analyze_text")
    return


def fob_stats():
    logger.info("89:task started: fob_stats")

    cmd = 'fob_stats'
    logpath = gen_output_name(cmd)
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command(cmd, '--mode OBJECT')

    logger.info("97:task ended: fob_stats")
    return


def fob_sync():
    logger.info("102:task started: fob_sync")

    cmd = 'fob_sync'
    logpath = gen_output_name(cmd)
    with open(logpath, 'a+') as outfile:
        with redirect_stdout(outfile):
            call_command(cmd, '--maxget 10')

    logger.info("110:task ended: fob_sync")
    return
