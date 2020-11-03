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

# Application imports

client = Client()

class HealthEndpointTests(SimpleTestCase):
    """ Health Endpoint used to validate Docker/Cloud deployment """

    def test_health_status_is_up(self):
        """ Test that health status is returned with RC=200 """

        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '{"status": "UP"}')
