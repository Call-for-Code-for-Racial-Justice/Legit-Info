#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/tests.py -- Perform simple tests

Written by James Stewart and Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
# Django and other third-party imports
import os
from unittest import mock

from django.test import Client
from django.core.management import call_command
from django.test import TestCase
from io import StringIO

# Application imports

client = Client()


class GetDatasetsCustomCommandtests(TestCase):
    @mock.patch.dict(os.environ, {"FOB_STORAGE": "/tmp/"})
    @mock.patch('cfc_app.legiscan_api.LegiscanAPI.get_datasetlist', return_value='{"status":"OK","datasetlist":[{"state_id":26,"session_id":1748,"year_start":2021,"year_end":2021,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2021 Regular Session","session_name":"2021 Regular Session","dataset_date":"2021-12-31","dataset_hash":"1ed379b4dd09328b21e5842ed3887f08","dataset_size":6074816,"access_key":"4EWZIj13Aq5ZblsrKe2WnL"},{"state_id":26,"session_id":1616,"year_start":2019,"year_end":2019,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2019 Regular Session","session_name":"2019 Regular Session","dataset_date":"2021-12-31","dataset_hash":"758271e29ef101e2acbbee4deeb58ef9","dataset_size":5617521,"access_key":"5LYnWXTQXlZQaPJpavqziU"},{"state_id":26,"session_id":1515,"year_start":2017,"year_end":2017,"prefile":0,"sine_die":1,"prior":1,"special":1,"session_tag":"1st Special Session","session_title":"2017 1st Special Session","session_name":"2017 1st Special Session","dataset_date":"2021-12-31","dataset_hash":"ac42d27b8508cd896b109dcc886f4250","dataset_size":159109,"access_key":"5tS6HLKFPzlOR5UVOaUGOk"},{"state_id":26,"session_id":1224,"year_start":2017,"year_end":2017,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2017 Regular Session","session_name":"2017 Regular Session","dataset_date":"2021-12-31","dataset_hash":"8e96118260969d33a2ca4901ddbc6b16","dataset_size":5132347,"access_key":"Uu2nIH0HV8feb4Ty0GKnD"},{"state_id":26,"session_id":1138,"year_start":2015,"year_end":2015,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2015 Regular Session","session_name":"2015 Regular Session","dataset_date":"2021-12-31","dataset_hash":"bc02a990e5572c5f5db6fec6c9498eab","dataset_size":5069664,"access_key":"3XlA78OO4nElKKmNm7jdfu"},{"state_id":26,"session_id":977,"year_start":2013,"year_end":2013,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2013 Regular Session","session_name":"2013 Regular Session","dataset_date":"2021-12-31","dataset_hash":"16254428bdfbd6331505e4df771e44d2","dataset_size":4301530,"access_key":"6UoW57rNyuiYU1bl6ww8Tf"},{"state_id":26,"session_id":85,"year_start":2011,"year_end":2011,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2011 Regular Session","session_name":"2011 Regular Session","dataset_date":"2021-12-31","dataset_hash":"a522cc9428c81f79dbe5e09d0f92c436","dataset_size":4352754,"access_key":"5onw8XXavRHI3dkKQTmW5s"},{"state_id":26,"session_id":56,"year_start":2009,"year_end":2009,"prefile":0,"sine_die":1,"prior":1,"special":0,"session_tag":"Regular Session","session_title":"2009 Regular Session","session_name":"2009 Regular Session","dataset_date":"2021-12-31","dataset_hash":"e493fce95901b10fd2bb3e3c1b9812d2","dataset_size":2165076,"access_key":"5VP5NrQxT7DALXMlSby7AB"}]}')
    def test_get_datasets(self, mock_get_datasetlist):
        out = StringIO()
        call_command('get_datasets', '--api', '--frequency', '1', stdout=out)

        # self.assertEqual(response.status_code, 200)
        # self.assertContains(response, '{"status": "UP"}')

# add_arguments
    def add_arguments(self):
        # Verify that we get the expected arguments with the proper types
        return

# recent_enough
    def recent_enough_with_with_api_file_more_than_one_week_old(self):
        return

    def recent_enough_with_api_failue(self):
        return

    def recent_enough_with_not_calling_api_with_valid_file(self):
        return

    def recent_enough_with_not_calling_api_without_valid_file(self):
        return

    def recent_enough_with_invalid_legiscan_file(self):
        return

    def recent_enough_with_no_legiscan_file(self):
        return

    def recent_enough_with_more_than_5_versions(self):
        return

# find_latest_dsl
    def find_latest_dsl_with_no_data_elements_for_name(self):
        return

    def find_latest_dsl_with_one_data_element_for_name(self):
        return

    def find_latest_dsl_with_multiple_data_elements_for_name(self):
        return

    def find_latest_dsl_with_multiple_data_elements_for_multiple_names(self):
        return

# fetch_dsl_api
    def fetch_dsl_api_with_no_data_returned(self):
        return

    def fetch_dsl_api_with_existing_data_returned(self):
        return

    def fetch_dsl_api_with_new_data_returned(self):
        return

# fetch_dataset
    def fetch_dataset_with_no_entries(self):
        return

    def fetch_dataset_with_no_entries_for_this_state(self):
        return

    def fetch_dataset_with_entry_for_this_state_with_no_entries_from_this_year(self):
        return

    def fetch_dataset_with_entry_for_this_state_with_entries_from_this_year(self):
        return

# fetch_from_api
    def fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_with_bad_api(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_with_bad_api(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_with_bad_api(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_with_bad_api(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_without_session_data(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_without_session_data(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_without_session_data(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_without_session_data(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api_with_error(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api_with_error(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api_with_error(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api_with_error(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_not_using_api(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_not_using_api(self):
        return

    def fetch_from_api_with_existing_session_with_existing_hash_code_when_using_api(self):
        return

    def fetch_from_api_with_existing_session_without_existing_hash_code_when_using_api(self):
        return

# datasets_found
    def datasets_found_with_no_states(self):
        return

    def datasets_found_with_states_without_matching_state_id(self):
        return

    def datasets_found_with_states_without_matching_year_end(self):
        return

    def datasets_found_with_states_with_equal_year_end(self):
        return

    def datasets_found_with_states_with_newer_year_end_in_entry(self):
        return

    def datasets_found_with_unmatched_session_name(self):
        return

    def datasets_found_with_matched_session_name(self):
        return
# Identify what test cases we want
# Potentially download the file once, and then use that as a base to test against if you had an account
# Ask the add-states tem for a sample file
# --api invokes Watson NLU, so we will want to mock that out
# look at the django offial docs on test writing
# obeythetestinggoat
# settings.py should have some details on where to look for tests
# could we extract documentation from our unit tests?
# There are some existing github actions, even one that runs tests with coverage, we might want to see if there's a better way to do it.
