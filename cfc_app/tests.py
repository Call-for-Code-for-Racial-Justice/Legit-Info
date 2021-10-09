#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/tests.py -- Perform simple tests

Written by James Stewart and Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
# Django and other third-party imports
from django.test import SimpleTestCase
from django.test import Client
from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from cfc_app.models import Location
from django.core.management.base import CommandError
from argparse import ArgumentError

# Application imports

client = Client()


class HealthEndpointTests(SimpleTestCase):
    """ Health Endpoint used to validate Docker/Cloud deployment """

    def test_health_status_is_up(self):
        """ Test that health status is returned with RC=200 """

        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '{"status": "UP"}')


class AddStatesCustomCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        locations = Location.objects.order_by('hierarchy')

        # If database is empty, re-create the "world" entry that acts as
        # the master parent for the ancestor-search.
        if len(locations) == 0:
            Location.load_defaults()

    def test_add_new_state(self):
        out = StringIO()
        state_name = 'CA'
        call_command('add_states', state_name, stdout=out)
        #test state was added
        state = Location.objects.get(shortname='ca')
        self.assertEqual(state.shortname, state_name.lower(), f'duh! {state_name} not found.')
        self.assertEqual(state.longname, 'California, USA', f'duh! {state.longname} incorrect.')
        self.assertEqual(state.legiscan_id, 5, f'duh! {state.legiscan_id} incorrect.')
        self.assertEqual(state.govlevel, 'state', f'duh! {state.govlevel} incorrect.')
        self.assertEqual(state.parent.shortname, 'usa', f'duh! {state.parent} incorrect.')

    def test_add_existing_state(self):
        out = StringIO()
        state_name = 'OH'
        state_oh_old = Location.objects.get(shortname='oh')
        call_command('add_states', state_name, stdout=out)
        #test there is still a single state
        self.assertEqual(len(Location.objects.filter(shortname='oh')), 1, 'Oh != 1')

    def test_add_multiple_states(self):
        out = StringIO()
        call_command('add_states', 'GA', 'MN', 'TX' , stdout=out)

        state = Location.objects.get(shortname='ga')
        self.assertEqual(state.shortname, 'ga', f'duh! ga not found.')
        self.assertEqual(state.longname, 'Georgia, USA', f'duh! {state.longname} incorrect.')
        self.assertEqual(state.legiscan_id, 10, f'duh! {state.legiscan_id} incorrect.')
        self.assertEqual(state.govlevel, 'state', f'duh! {state.govlevel} incorrect.')
        self.assertEqual(state.parent.shortname, 'usa', f'duh! {state.parent} incorrect.')

        state = Location.objects.get(shortname='mn')
        self.assertEqual(state.shortname, 'mn', f'duh! mn not found.')
        self.assertEqual(state.longname, 'Minnesota, USA', f'duh! {state.longname} incorrect.')
        self.assertEqual(state.legiscan_id, 23, f'duh! {state.legiscan_id} incorrect.')
        self.assertEqual(state.govlevel, 'state', f'duh! {state.govlevel} incorrect.')
        self.assertEqual(state.parent.shortname, 'usa', f'duh! {state.parent} incorrect.')

        state = Location.objects.get(shortname='tx')
        self.assertEqual(state.shortname, 'tx', f'duh! tx not found.')
        self.assertEqual(state.longname, 'Texas, USA', f'duh! {state.longname} incorrect.')
        self.assertEqual(state.legiscan_id, 43, f'duh! {state.legiscan_id} incorrect.')
        self.assertEqual(state.govlevel, 'state', f'duh! {state.govlevel} incorrect.')
        self.assertEqual(state.parent.shortname, 'usa', f'duh! {state.parent} incorrect.')



    def test_no_args_should_fail(self):
        out = StringIO()
        self.assertRaises((CommandError, ArgumentError), call_command, 'add_states', stdout=out)

    def test_add_non_state_should_fail(self):
        out = StringIO()
        state_name = 'OO'
        self.assertRaises((CommandError, ArgumentError), call_command, 'add_states', state_name, stdout=out)
