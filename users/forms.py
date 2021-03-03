#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
users/forms.py -- Input forms for GUI.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
# Django and other third-party imports
from django import forms
from django.contrib.auth.models import User

# Application imports
from cfc_app.models import Location, Impact
from .models import Profile


class UserForm(forms.ModelForm):
    """ Input form user registration """

    class Meta:
        """ fields involved in the form """
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    """ Input form user profile """

    class Meta:
        """ fields involved in the form """
        model = Profile
        fields = ('location', 'impacts')

    location = forms.ModelChoiceField(
        queryset=Location.objects.all().exclude(shortname='world'),
        empty_label='Please select a location'
    )

    impacts = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Impact.objects.all().exclude(iname='None')
    )
