#!/usr/bin/env python3
# ShowProgress.py -- print dots across the screen
# By Tony Pearson, IBM, 2020
#
import sys
from django.conf import settings
from cfc_app.FOB_Storage import FOB_Storage


class Oneline():
    """ Class to maintain one long line in a file with no line breaks  """

    def __init__(self):
        """ Set characters to use for showing progress"""
        self.oneline = ''
        return None

    def add_text(self, line):
        newline = line.replace('\u2011', '-').replace('\u2013', '-')
        newline = newline.replace('\u2019', '-')
        # newline = newline.replace("'", "-").replace('"', '_').splitlines()
        newline2 = ' '.join(newline)
        self.oneline += newline2 + ' '
        return self

    def write_name(self, outname):
        fob = FOB_Storage(settings.FOB_METHOD)
        self.oneline = self.oneline.replace(". ", '.\n')
        fob.upload_text(self.oneline, outname, codec='UTF-8')
        return self


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    text_line = Oneline()
    text_line.add_text('Line "with" double quotes.')
    text_line.add_text("Line 'with' single quotes.")
    print("===["+text_line.oneline+"]===")
    text_line.write_name('test-file.txt')

    print('Congratulations')
