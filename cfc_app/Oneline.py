#!/usr/bin/env python3
# Oneline.py -- process text file as a single one-line string
# By Tony Pearson, IBM, 2020
#
import nltk
import sys


class Oneline():
    """ Class to maintain one long line in a file with no line breaks  """

    def __init__(self, nltk_loaded=False):
        """ Set characters to use for showing progress"""
        self.oneline = ''
        if not nltk_loaded:
            nltk.download('punkt')
        self.nltk_loaded = True
        return None

    def add_text(self, line):
        newline = line.replace('\u2011', '-').replace('\u2013', '-')
        newline = newline.replace('\u2019', '-')
        # newline = newline.replace("'", "-").replace('"', '_')
        newlines = newline.splitlines()
        newline2 = ' '.join(newlines)
        self.oneline += newline2 + ' '
        return self

    def split_sentences(self):
        a_list = nltk.tokenize.sent_tokenize(self.oneline)
        self.oneline = '\n'.join(a_list)
        return self


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    text_line = Oneline()
    text_line.add_text('Line "with" double quotes.')
    text_line.add_text("Line 'with' single quotes.")
    print("===["+text_line.oneline+"]===")

    print(' ')
    print('Split sentences:')
    text_line.split_sentences()
    print("===["+text_line.oneline+"]===")

    print('Congratulations')
