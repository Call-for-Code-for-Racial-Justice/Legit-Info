#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use APP_NAME in all screens.

When application was renamed from "Fix Politics" to "Legit Info",
this tag was created so that APP_NAME set in cfc_project/settings.py
would be propagated to all screens.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def app_name(request):
    """ return APP_NAME from Django settings """

    if request is None:     # Eliminate pylint errors
        pass
    return settings.APP_NAME
