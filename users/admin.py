#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
users/admin.py -- Decide what appears on Admin screen

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
from django.contrib import admin
from django.contrib.auth.models import Group

# Register your models here.
from .models import Profile

admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """ Specify columns to display """
    list_display = ("user", "criteria")
