#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/test_get_datasets.py -- Characterization of behaviour on get_datasets custom command

Written by Robert Bruce, 2022
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import datetime
import os

# Django and other third-party imports
from unittest import mock
from unittest.mock import call

import mockito
from mockito import when, verify, times
from django.conf import LazySettings
from django.test import Client
from django.test import TestCase

# Application imports
import cfc_app
from cfc_app.management.commands.get_datasets import Command

client = Client()


class GetDatasetsCustomCommandTests(TestCase):
    @classmethod
    def setUp(cls):
        os.environ['FOB_STORAGE'] = '/tmp/'
        cls.subject = Command()

        when(cfc_app.management.commands.get_datasets).save_entry_to_hash(...).thenReturn()
        when(cls.subject.fob).upload_text(...).thenReturn()

    @classmethod
    def tearDown(cls):
        mockito.unstub(cls.subject)
        mockito.unstub(cfc_app.management.commands.get_datasets)

# add_arguments
    @mock.patch("django.core.management.base.CommandParser")
    def test_add_arguments(self, parser):
        self.subject.add_arguments(parser);

        parser.add_argument.assert_has_calls([
            call("--api", action="store_true",
                                help="Invoke Legiscan.com API"),
            call("--state", help="Process single state: AZ, OH"),
            call("--frequency", type=int, default=self.subject.frequency,
                                help="Days since last DatasetList request")])
        return

# find_latest_dsl
    def test_find_latest_dsl_with_no_data_elements_for_name(self):
        self.subject.dsl_list = ["TestNameThatDoesn'tWork"]
        self.subject.find_latest_dsl()

        self.assertEqual(LazySettings().LONG_AGO, self.subject.latest_date)
        self.assertIsNone(self.subject.latest_name)

    def test_find_latest_dsl_with_one_data_element_for_name(self):
        self.subject.dsl_list = ["DatasetList-2020-01-30.json"]

        self.subject.find_latest_dsl()

        self.assertEqual(datetime.datetime.fromisoformat("2020-01-30").date(), self.subject.latest_date)
        self.assertEqual("DatasetList-2020-01-30.json", self.subject.latest_name)

    def test_find_latest_dsl_with_multiple_data_elements_for_name(self):
        self.subject.dsl_list = ["DatasetList-2020-01-30.json", "DatasetList-2020-01-30.json"]

        self.subject.find_latest_dsl()

        self.assertEqual(datetime.datetime.fromisoformat("2020-01-30").date(), self.subject.latest_date)
        self.assertEqual("DatasetList-2020-01-30.json", self.subject.latest_name)

    def test_find_latest_dsl_with_multiple_data_elements_for_multiple_names(self):
        self.subject.dsl_list = ["DatasetList-2020-01-30.json", "DatasetList-2020-01-31.json"]

        self.subject.find_latest_dsl()

        self.assertEqual(datetime.datetime.fromisoformat("2020-01-31").date(), self.subject.latest_date)
        self.assertEqual("DatasetList-2020-01-31.json", self.subject.latest_name)

# fetch_dsl_api
    def test_fetch_dsl_api_with_no_data_returned(self):
        self.subject.now = datetime.datetime.fromisoformat("2020-01-30").date()
        when(self.subject.leg).get_datasetlist('Good').thenReturn([])
        self.subject.dsl_list = []
        self.subject.fetch_dsl_api()
        self.assertFalse(self.subject.dsl_list)

    def test_fetch_dsl_api_with_existing_data_returned(self):
        self.subject.now = datetime.datetime.fromisoformat("2020-01-30").date()
        when(self.subject.leg).get_datasetlist('Good').thenReturn(["TestItem"])

        self.subject.dsl_list = ['DatasetList-2020-01-30.json']
        self.subject.fetch_dsl_api()
        self.assertListEqual(self.subject.dsl_list, ['DatasetList-2020-01-30.json'])

    def test_fetch_dsl_api_with_new_data_returned(self):
        self.subject.now = datetime.datetime.fromisoformat("2020-01-30").date()
        when(self.subject.leg).get_datasetlist('Good').thenReturn(["TestItem"])

        self.subject.dsl_list = []
        self.subject.fetch_dsl_api()
        self.assertListEqual(self.subject.dsl_list, ['DatasetList-2020-01-30.json'])

# fetch_dataset
    def test_fetch_dataset_with_no_entries(self):
        self.subject.datasetlist = {}
        when(self.subject).fetch_from_api(...).thenReturn()
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject, times=0).fetch_from_api(...)

    def test_fetch_dataset_with_no_entries_for_this_state(self):
        self.subject.datasetlist = [{'state_id': 'SomeOtherState',
                                    'session_id': 1234,
                                    'year_end': 2020}]
        when(self.subject).fetch_from_api(...).thenReturn()
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject, times=0).fetch_from_api(...)

    def test_fetch_dataset_with_entry_for_this_state_with_no_entries_from_this_year(self):
        self.subject.fromyear = 2020
        self.subject.datasetlist = [{'state_id': 'TestStateID',
                                     'session_id': 1234,
                                     'year_end': 2015}]
        when(self.subject).fetch_from_api(...).thenReturn()
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject, times=0).fetch_from_api(...)

    def test_fetch_dataset_with_entry_for_this_state_with_entries_from_this_year(self):
        self.subject.fromyear = 2010
        entry = {'state_id': 'TestStateID',
                'session_id': 1234,
                'year_end': 2015}
        self.subject.datasetlist = [entry]
        when(self.subject).fetch_from_api(...).thenReturn()
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject).fetch_from_api('TestState-Dataset-1234.json', entry)

# datasets_found
    def test_datasets_found_with_no_states(self):
        self.subject.datasets_found([])
        verify(cfc_app.management.commands.get_datasets, times=0).save_entry_to_hash(...)

    def test_datasets_found_with_states_without_matching_state_id(self):
        when(self.subject.fobhelp).dataset_items('TestState').thenReturn('TestState-Dataset-1234.json')

        entry = {'state_id': 'UnmatchedStateID',
                 'session_id': 1234,
                 'year_start': 2014,
                 'year_end': 2015,
                 'dataset_size': 0}
        self.subject.fromyear = 2020
        self.subject.datasetlist = [entry]
        self.subject.datasets_found([['TestState', 'TestStateID']])
        verify(cfc_app.management.commands.get_datasets, times=0).save_entry_to_hash(...)

    def test_datasets_found_with_states_without_matching_year_end(self):
        when(self.subject.fobhelp).dataset_items('TestState').thenReturn('TestState-Dataset-1234.json')

        entry = {'state_id': 'TestStateID',
                 'session_id': 1234,
                 'dataset_date': '2015-01-30',
                 'year_start': 2014,
                 'year_end': 2015,
                 'dataset_size': 0}
        self.subject.fromyear = 2020
        self.subject.datasetlist = [entry]
        self.subject.datasets_found([['TestState', 'TestStateID']])
        verify(cfc_app.management.commands.get_datasets, times=0).save_entry_to_hash(...)

    def test_datasets_found_with_states_with_equal_year_end(self):
        when(self.subject.fobhelp).dataset_items('TestState').thenReturn('TestState-Dataset-1234.json')

        entry = {'state_id': 'TestStateID',
                 'session_id': 1234,
                 'dataset_date': '2015-01-30',
                 'year_start': 2014,
                 'year_end': 2015,
                 'dataset_size': 0}
        self.subject.fromyear = 2015
        self.subject.datasetlist = [entry]

        self.subject.datasets_found([['TestState', 'TestStateID']])
        verify(cfc_app.management.commands.get_datasets).save_entry_to_hash(...)

    def test_datasets_found_with_states_with_newer_year_end_in_entry(self):
        when(self.subject.fobhelp).dataset_items('TestState').thenReturn('TestState-Dataset-1234.json')

        entry = {'state_id': 'TestStateID',
                 'session_id': 1234,
                 'dataset_date': '2015-01-30',
                 'year_start': 2014,
                 'year_end': 2015,
                 'dataset_size': 0}
        self.subject.fromyear = 2014
        self.subject.datasetlist = [entry]

        self.subject.datasets_found([['TestState', 'TestStateID']])
        verify(cfc_app.management.commands.get_datasets).save_entry_to_hash(...)

    def test_datasets_found_with_unmatched_session_name(self):
        when(self.subject.fobhelp).dataset_items('TestState').thenReturn('UnmatchedSessionName')

        entry = {'state_id': 'TestStateID',
                 'session_id': 1234,
                 'dataset_date': '2015-01-30',
                 'year_start': 2014,
                 'year_end': 2015,
                 'dataset_size': 0}
        self.subject.fromyear = 2015
        self.subject.datasetlist = [entry]

        self.subject.datasets_found([['TestState', 'TestStateID']])
        verify(cfc_app.management.commands.get_datasets, times=0).save_entry_to_hash(...)
