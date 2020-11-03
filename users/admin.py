#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
users/admin.py -- Decide what appears on Admin screen

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
from django.contrib import admin

# Register your models here.
from .models import Profile

admin.site.register(Profile)
