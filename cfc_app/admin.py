#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/admin.py -- Decide what appears on Admin screen

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
from django.contrib import admin

# Register your models here.
from .models import Location, Impact, Criteria, Law, Hash


class CriteriaAdmin(admin.ModelAdmin):
    """ Admin for cfc_app_criteria """
    pass


class HashAdmin(admin.ModelAdmin):
    """ Admin for cfc_app_hash """
    list_display = ("item_name", "fob_method", "generated_date", "hashcode",
                    "size")
    search_fields = ("item_name", "generated_date")


class ImpactAdmin(admin.ModelAdmin):
    """ Admin for cfc_app_impact """
    pass


class LawAdmin(admin.ModelAdmin):
    """ Admin for cfc_app_law """

    list_display = ("key", "loc_desc", "impact", "title")
    list_filter = ("impact", "location")
    search_fields = ("key", "title", "summary")
    fields = ("key", "location", "impact", "title", "cite_url", "relevance",
              "summary", "doc_date", "bill_id")

    def loc_desc(self, obj):
        """ Get location description """
        if self is None:
            pass
        loc = obj.location
        return loc.desc

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """ Override formfield for text areas """

        field = super(LawAdmin, self).formfield_for_dbfield(db_field, request,
                                                            **kwargs)
        if db_field.name == 'title':
            field.widget.attrs['rows'] = 2
        if db_field.name == 'summary':
            field.widget.attrs['rows'] = 10
        if db_field.name == 'relevance':
            field.widget.attrs['rows'] = 3
        return field


class LocationAdmin(admin.ModelAdmin):
    """ Admin for cfc_app_location """

    list_display = ("desc", "govlevel", "hierarchy", "legiscan_id")
    fields = ("desc", "shortname", "govlevel", "legiscan_id", "hierarchy",
              "parent")


admin.site.register(Criteria, CriteriaAdmin)
admin.site.register(Hash, HashAdmin)
admin.site.register(Impact, ImpactAdmin)
admin.site.register(Law, LawAdmin)
admin.site.register(Location, LocationAdmin)
