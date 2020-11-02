#!/usr/bin/env python3
# DataBundle.py -- to handle API requests / responses
# By Tony Pearson, IBM, 2020
#
# Debug with:  import pdb; pdb.set_trace()

import requests
import sys


class DataBundle():
    """
    Class to show progress in long-running tasks

    from ShowProgress import ShowProgress
    dot = ShowProgress()
    dot.show()  # print a single character to show progress
    dot.end()  # End the sequence, print newline

    Default character is period(.), you can change the character:
        dot = ShowProgress(dotchar="#")
    """

    def __init__(self, name):
        """ Set characters to use for showing progress"""
        self.name = name
        self.ok = False
        self.status_code = None
        self.headers = None
        self.mime_type = None
        self.extension = None
        self.content = None
        self.text = None
        self.json_pkg = None
        return None

    def __repr__(self):
        dispForm1 = "Bundle {}: OK={} Code={}"
        dispForm2 = '{}  {}{}'
        dispForm3 = '{}  Length={} bytes'
        display = dispForm1.format(self.name, self.ok, self.status_code)
        if self.ok:
            if self.extension:
                display = dispForm2.format(display, 'ext:', self.extension)
            else:
                display = dispForm2.format(display, 'mime:', self.mime_type)
            if self.content:
                display = dispForm3.format(display, len(self.content))
        return display

    def make_request(self, url, params):
        response = requests.get(url, params)
        return response

    def load_response(self, response):
        """ Display a single dot """
        self.ok = response.ok
        self.status_code = response.status_code
        self.headers = response.headers
        self.mime_type = self.headers['Content-Type']
        self.content = response.content
        if 'html' in self.mime_type:
            self.extension = 'html'
            self.text = response.text
        if 'json' in self.mime_type:
            self.extension = 'json'
            self.json_pkg = response.json()
            self.text = response.text
        if 'pdf' in self.mime_type:
            self.extension = 'pdf'
            if self.content[:4] != b'%PDF':
                self.ok = False
                self.extension = 'error'
                self.name += " *NOT PDF*"
                self.status_code = 406
        return response.ok


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    bundle = DataBundle('ibm.com')
    params = {}
    response = bundle.make_request('http://www.ibm.com', params)
    print('RESPONSE: ', response)
    result = bundle.load_response(response)
    print('RESULT:', result)
    print('BUNDLE:', bundle)

    print('Congratulations')
