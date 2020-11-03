#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/apps.py -- Define apps for module search.

Since the name of this application could change, we have
used the generic 'cfc_app' to refer to Call-for-Code.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# Django and other third-party imports
from django.apps import AppConfig


class CFCappConfig(AppConfig):
    """ Set application name """
    name = 'cfc_app'
