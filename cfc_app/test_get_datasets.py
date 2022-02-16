#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/tests.py -- Perform simple tests

Written by James Stewart and Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
# Django and other third-party imports
import datetime
import os
from unittest import mock
from unittest.mock import call

import mockito
from mockito import when, verify, times
from django.conf import LazySettings
from django.test import Client
from django.test import TestCase

from cfc_app.management.commands.get_datasets import Command
# Application imports

client = Client()


class GetDatasetsCustomCommandTests(TestCase):
    @classmethod
    def setUp(cls):
        os.environ['FOB_STORAGE'] = '/tmp/'
        cls.subject = Command()

        when(cls.subject.fob).upload_text(...).thenReturn()

    @classmethod
    def tearDownClass(cls):
        mockito.unstub(cls.subject)

    # def test_test_get_datasets(self, mock_get_datasetlist):
    #     out = StringIO()
    #     call_command('get_datasets', '--api', '--frequency', '1', stdout=out)

        # self.assertEqual(response.status_code, 200)
        # self.assertContains(response, '{"status": "UP"}')

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

# recent_enough
    def test_recent_enough_with_with_api_file_more_than_one_week_old(self):
        now = self.subject.now

        return

    def test_recent_enough_with_api_failue(self):
        return

    def test_recent_enough_with_not_calling_api_with_valid_file(self):
        return

    def test_recent_enough_with_not_calling_api_without_valid_file(self):
        return

    def test_recent_enough_with_invalid_legiscan_file(self):
        return

    def test_recent_enough_with_no_legiscan_file(self):
        return

    def test_recent_enough_with_more_than_5_versions(self):
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
        self.subject.fetch_from_api = mockito.mock(self.subject.fetch_from_api)
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject.fetch_from_api, times=0).__call__(...)

    def test_fetch_dataset_with_no_entries_for_this_state(self):
        self.subject.datasetlist = [{'state_id': 'SomeOtherState',
                                    'session_id': 1234,
                                    'year_end': 2020}]
        self.subject.fetch_from_api = mockito.mock(self.subject.fetch_from_api)
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject.fetch_from_api, times=0).__call__(...)

    def test_fetch_dataset_with_entry_for_this_state_with_no_entries_from_this_year(self):
        self.subject.fromyear = 2020
        self.subject.datasetlist = [{'state_id': 'TestStateID',
                                     'session_id': 1234,
                                     'year_end': 2015}]
        self.subject.fetch_from_api = mockito.mock(self.subject.fetch_from_api)
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject.fetch_from_api, times=0).__call__(...)

    def test_fetch_dataset_with_entry_for_this_state_with_entries_from_this_year(self):
        self.subject.fromyear = 2010
        entry = {'state_id': 'TestStateID',
                'session_id': 1234,
                'year_end': 2015}
        self.subject.datasetlist = [entry]
        when(self.subject).fetch_from_api(...).thenReturn()
        self.subject.fetch_dataset('TestState', 'TestStateID')

        verify(self.subject).fetch_from_api('TestState-Dataset-1234.json', entry)

# fetch_from_api
    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_with_bad_api(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_with_bad_api(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_with_bad_api(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_with_bad_api(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_without_session_data(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_without_session_data(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_without_session_data(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_without_session_data(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_with_error(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_with_error(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_with_error(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_with_error(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api(self):
        return

    def test_fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api(self):
        return

    def test_fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api(self):
        return

# datasets_found
    def test_datasets_found_with_no_states(self):
        return

    def test_datasets_found_with_states_without_matching_state_id(self):
        return

    def test_datasets_found_with_states_without_matching_year_end(self):
        return

    def test_datasets_found_with_states_with_equal_year_end(self):
        return

    def test_datasets_found_with_states_with_newer_year_end_in_entry(self):
        return

    def test_datasets_found_with_unmatched_session_name(self):
        return

    def test_datasets_found_with_matched_session_name(self):
        return

# --api invokes Watson NLU, so we will want to mock that out
# look at the django offial docs on test writing
# obeythetestinggoat
# could we extract documentation from our unit tests?
# There are some existing github actions, even one that runs tests with coverage, we might want to see if there's a better way to do it.
