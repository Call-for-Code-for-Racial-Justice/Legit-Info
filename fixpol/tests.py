# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django.test import Client
client = Client()


class HealthEndpointTests(SimpleTestCase):
    def test_health_status_is_up(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '{"status": "UP"}')
