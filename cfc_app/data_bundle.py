#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to handle data resulting from API requests / responses

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import certifi
import logging
import sys
import urllib3

# Django and other third-party imports
import requests

# Application imports

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class DataBundle():
    """
    Class to handle API requests / responses

    """

    def __init__(self, name):

        self.name = name
        self.status_ok = False
        self.status_code = None
        self.headers = None
        self.mime_type = None
        self.extension = None
        self.content = None
        self.msgtext = None
        self.json_pkg = None
        return None

    def __repr__(self):
        """ Representation in display format """

        display = (f"Bundle {self.name}: OK={self.status_ok} "
                   f"Code={self.status_code} ")
        if self.status_ok:
            if self.extension:
                display += f"ext: {self.extension} "
            else:
                display += f"mime: {self.mime_type} "

            if self.content:
                display += f"Length= {len(self.content)} bytes"

        return display

    def make_request(self, url, params):
        """ Make API request and capture the response """

        logger.debug(f"Make request {self.name}")
        # Issue 72 add ca_cert verification, bypass for Ohio
        ca_cert = certifi.where()
        if 'state.oh.us' in url or 'mn.gov' in url:
            ca_cert = False
            urllib3.disable_warnings()
        # import pdb; pdb.set_trace()
        response = requests.get(url, params, verify=ca_cert) 
        return response

    def load_response(self, response):
        """ save response values with data bundle """

        self.status_ok = response.ok
        self.status_code = response.status_code
        self.headers = response.headers
        self.mime_type = self.headers['Content-Type']
        self.content = response.content
        if 'html' in self.mime_type:
            self.extension = 'html'
            self.msgtext = response.text
        if 'json' in self.mime_type:
            self.extension = 'json'
            self.json_pkg = response.json()
            self.msgtext = response.text
        if 'pdf' in self.mime_type:
            self.extension = 'pdf'
            if self.content[:4] != b'%PDF':
                self.status_ok = False
                self.extension = 'error'
                self.name += " *NOT PDF*"
                self.status_code = 406
        return self.status_ok


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    bundle = DataBundle('ibm.com')
    params = {}
    response = bundle.make_request('https://www.ibm.com', params)
    print('RESPONSE: ', response)
    result = bundle.load_response(response)
    print('RESULT:', result)
    print('BUNDLE:', bundle)

    bundle = DataBundle('state.oh.us')
    params = {'format': 'pdf'}
    response = bundle.make_request('https://search-prod.lis.state.oh.us/solarapi/v1/general_assembly_134/bills/hb13/IN/00', params)
    print('RESPONSE: ', response)
    result = bundle.load_response(response)
    print('RESULT:', result)
    print('BUNDLE:', bundle)

    print('Congratulations')
