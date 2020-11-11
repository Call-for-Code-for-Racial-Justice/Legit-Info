#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/tests_class.py -- Perform simple tests on support classes

Written by James Stewart and Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
from io import StringIO
import time
from unittest.mock import patch

# Django and other third-party imports
from django.test import SimpleTestCase
from cfc_app.show_progress import ShowProgress

# Application imports


class TestShowProgress(SimpleTestCase):
    """ Testcases for show_progress.py """

    def test_dot_gets_to_stdout(self):
        """ Verify standard dots """

        expected_out = "....\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            dot = ShowProgress()
            for _ in range(3):
                dot.show()
                time.sleep(0.3)
            dot.end()
            self.assertEqual(fake_out.getvalue(), expected_out)

    def test_dotchar_gets_to_stdout(self):
        """ Override default character with hashtag (#) instead """

        expected_out = "####\n"
        with patch('sys.stdout', new=StringIO()) as fake_out:
            dash = ShowProgress(dotchar='#')
            for _ in range(3):
                dash.show()
                time.sleep(0.2)
            dash.end()
            self.assertEqual(fake_out.getvalue(), expected_out)

    def test_change_midway(self):
        """ Change character midway to show progress """

        expected_out = "####@@@@@@@\n"
        with patch('sys.stdout', new=StringIO()) as fake_out:
            hashtag = ShowProgress(dotchar="#")
            for num in range(10):
                hashtag.show()
                if num >= 3:
                    hashtag.dotchar = "@"
                time.sleep(0.1)
            hashtag.end()
            self.assertEqual(fake_out.getvalue(), expected_out)

# end of tests
