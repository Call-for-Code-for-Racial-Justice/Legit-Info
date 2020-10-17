#!/usr/bin/env python3
# ShowProgress.py -- print dots across the screen
# By Tony Pearson, IBM, 2020
#
import sys

class Oneline():
    """ Class to maintain one long line in a file with no line breaks  """

    def __init__(self):
        """ Set characters to use for showing progress"""
        self.oneline = ''
        return None

    def add_text(self, line):
        newline = line.replace("'", " ").replace('"', ' ').splitlines()
        newline2 = ' '.join(newline)
        self.oneline += newline2 + ' '
        return self

    def write_file(self, outfile):
        print(self.oneline, end='', file=outfile)
        return self

    def write_name(self, outname):
        with open(outname, "w") as outfile:
            self.write_file(outfile)
        return self

if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    text_line = Oneline()
    text_line.add_text('Line "with" double quotes. ')
    text_line.add_text("Line 'with' single quotes.")
    print("===["+text_line.oneline+"]===")
    print('Congratulations')
