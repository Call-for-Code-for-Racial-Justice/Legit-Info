#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/forms.py -- Input forms for GUI.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
# Django and other third-party imports
from django import forms
from cfc_app.models import Location, Impact

# Application imports
from .models import Criteria


class SearchForm(forms.ModelForm):
    """ Input form to search legislation """

    class Meta:
        """ set model criteria """
        model = Criteria
        fields = ('location', 'impacts')

    location = forms.ModelChoiceField(
        queryset=Location.objects.exclude(shortname='world'),
        empty_label='Please select a location'
    )

    impacts = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Impact.objects.all().exclude(iname='None')
    )

    def __init__(self, *args, **kwargs):
        """Specify location and impact pull down menus """
        super().__init__(*args, **kwargs)

        # if you want to do just one
        self.fields['location'].error_messages = {
            'required': 'A location must be selected'}
        self.fields['impacts'].error_messages = {
            'required': 'Select one or more impact areas'}

# end of module
