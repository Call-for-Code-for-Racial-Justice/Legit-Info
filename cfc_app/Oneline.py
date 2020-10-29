#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to create file as a single text line.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging
logger = logging.getLogger(__name__)
import nltk
import re
import sys

# Debug with:  import pdb; pdb.set_trace()


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

    def header_file_name(self, filename):
        self.add_text("_FILE_ "+filename)
        return self

    def header_hash_code(self, hashcode):
        self.add_text(" _HASHCODE_ "+hashcode)
        return self

    def header_doc_date(self, docdate):
        self.add_text(" _DOCDATE_ "+docdate)
        return self

    def header_bill_id(self, bill_id):
        self.add_text(" _BILLID_ {}".format(bill_id))
        return self

    def header_cite_url(self, cite_url):
        self.add_text(" _CITE_ "+cite_url)
        return self

    def header_title(self, title):
        self.add_text(" _TITLE_ "+title)
        return self

    def header_summary(self, summary):
        self.add_text(" _SUMMARY_ "+summary)
        return self

    def header_end(self):
        self.add_text(' _TEXT_ ')
        return self

    def join_sentences(lines):
        newlines = lines.splitlines()
        line = ' '.join(newlines)
        return line

    def parse_header(text):
        """ Parse headers at the beginning of text file """

        FILE_REGEX = re.compile(r"_FILE_\s*(.*?)_")
        DOCDATE_REGEX = re.compile(r"_DOCDATE_\s*(.*?)_")
        HASHCODE_REGEX = re.compile(r"_HASHCODE_\s*(.*?)_")
        BILLID_REGEX = re.compile(r"_BILLID_\s*(.*?)_")
        CITE_REGEX = re.compile(r"_CITE_\s*(.*?)_")
        TITLE_REGEX = re.compile(r"_TITLE_\s*(.*?)_")
        SUMMARY_REGEX = re.compile(r"_SUMMARY_\s*(.*?)_")

        header = {}
        # import pdb; pdb.set_trace()
        newline = Oneline.join_sentences(text)
        sections = newline.split('_TEXT_')
        logger.debug(newline[:80])
        try:
            x = len(sections[1])
        except Exception as e:
            logger.error("Headers not found in text file".format(e), 
                          exc_info=True)
            raise RuntimeError

        if len(sections) == 2:
            head_text = sections[0] + "_TEXT_"
            mo = FILE_REGEX.search(head_text)
            if mo:
                header['FILE'] = mo.group(1).strip()

            mo = DOCDATE_REGEX.search(head_text)
            if mo:
                header['DOCDATE'] = mo.group(1).strip()

            mo = HASHCODE_REGEX.search(head_text)
            if mo:
                header['HASHCODE'] = mo.group(1).strip()

            mo = BILLID_REGEX.search(head_text)
            if mo:
                header['BILLID'] = mo.group(1).strip()

            mo = CITE_REGEX.search(head_text)
            if mo:
                header['CITE'] = mo.group(1).strip()
            elif 'FILE' in header:
                state = header['FILE'][:2]
                header['CITE'] = 'Legiscan.com/' + state

            mo = TITLE_REGEX.search(head_text)
            if mo:
                header['TITLE'] = mo.group(1).strip()

            mo = SUMMARY_REGEX.search(head_text)
            if mo:
                header['SUMMARY'] = mo.group(1).strip()       
            # import pdb; pdb.set_trace()
        return header


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

    paragraph = ("_FILE_ OH-SB66-1422-Y2017.pdf  _BILLID_ 968725  "
                "_DOCDATE_ 2018-07-09  "
                "_HASHCODE_ 758a357a208dd4385fe1c7cc93c6fb7e  "
                "_CITE_ http://search-prod.lis.state.oh.us/968725.pdf "
                "_TITLE_ Modify Criminal Sentencing and Corrections Law  "
                "_SUMMARY_ To authorize state-owned real estate.\n "
                "This triumph attests to the resolve of these people.\n "
                "_TEXT_ This is the start of the bill.")
    head = Oneline.parse_header(paragraph)
    print(head)


    print('Congratulations')
