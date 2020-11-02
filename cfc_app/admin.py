#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/admin.py -- Search and Display legislation

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
from django.contrib import admin

# Register your models here.
from .models import Location, Impact, Criteria, Law, Hash

admin.site.register(Location)
admin.site.register(Impact)
admin.site.register(Criteria)
admin.site.register(Law)
admin.site.register(Hash)
