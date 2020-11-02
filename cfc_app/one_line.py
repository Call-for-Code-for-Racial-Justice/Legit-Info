#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to create file as a single text line.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging
import re
import sys

# Django and other third-party imports
import nltk

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

FILE_REGEX = re.compile(r"_FILE_\s*(.*?) _")
DOCDATE_REGEX = re.compile(r"_DOCDATE_\s*(.*?) _")
HASHCODE_REGEX = re.compile(r"_HASHCODE_\s*(.*?) _")
BILLID_REGEX = re.compile(r"_BILLID_\s*(.*?) _")
CITE_REGEX = re.compile(r"_CITE_\s*(.*?) _")
TITLE_REGEX = re.compile(r"_TITLE_\s*(.*?) _")
SUMMARY_REGEX = re.compile(r"_SUMMARY[_]?\s*(.*?) _")

class OnelineError(RuntimeError):
    """ Customize error for this class """
    pass


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
        """ append a line to the existing file """

        newline = line.replace('\u2011', '-').replace('\u2013', '-')
        newline = newline.replace('\u2019', '-')
        newlines = newline.splitlines()
        newline2 = ' '.join(newlines)
        self.oneline += newline2 + ' '
        return self

    def split_sentences(self):
        """ Use Natural Language Toolkit (NLTK) to split into sentences. """

        newline = self.oneline
        header = ""
        if "\n" in newline:
            newline = Oneline.join_lines(newline)

        newline = Oneline.common_acronyms(newline)

        if "_TEXT_" in newline:
            sections = newline.split('_TEXT_')
            if "_SUMMARY_" in sections[0]:
                headings = sections[0].split("_SUMMARY_")
                front = headings[0]
                summary = Oneline.common_acronyms(headings[1])
            else:
                front, summary = sections[0], ""

            header = "{} _SUMMARY_ {} _TEXT_ \n".format(front, summary)
            newline = Oneline.common_acronyms(sections[1])

        a_list = nltk.tokenize.sent_tokenize(newline)
        c_list, merges = Oneline.merge_sentences(a_list)
        a_list = c_list

        logger.debug(f"61:Merges={merges} Lines={len(a_list)}")

        self.oneline = header + '\n'.join(a_list)
        return self

    @staticmethod
    def common_acronyms(line):
        """ Convert acronyms and bad character strings before NLTK """
        newline = line.replace(r'\x91', '')

        # Convert "H. B. No. 3" to "HB3"
        newline = re.sub(r"H.\s*B.\s*No.\s*(\d)", r"HB\1", newline)
        newline = re.sub(r"S.\s*B.\s*No.\s*(\d)", r"SB\1", newline)
        newline = re.sub(r"H.\s*R.\s*No.\s*(\d)", r"HR\1", newline)
        newline = re.sub(r"S.\s*R.\s*No.\s*(\d)", r"SR\1", newline)
        newline = re.sub(r"C.\s*R.\s*No.\s*(\d)", r"CR\1", newline)
        newline = re.sub(r"J.\s*R.\s*No.\s*(\d)", r"JR\1", newline)

        # Convert "H. B. 3" to "HB3"
        newline = re.sub(r"H.\s*B.\s*(\d)", r"HB\1", newline)
        newline = re.sub(r"S.\s*B.\s*(\d)", r"SB\1", newline)
        newline = re.sub(r"Am.\sSub.", r"Am-Sub", newline)

        # Convert General Assembly to avoid confusion with state of Georgia
        newline = re.sub(r"(st|nd|rd|th) G.A.", r"\1-GA ", newline)

        # Convert Sec. Sub. etc. to Sec# Sub#
        newline = re.sub(r"(Sec|Sub|SEC)[.]\s*([0-9]+)", r" \1#\2 ", newline)

        # Remove sections NN-NNNN.NN
        newline = re.sub(r"[0-9]+[-][0-9]+[.][0-9]+", r" ", newline)

        # Remove sections "(NNNN.MMM)"
        newline = re.sub(r"[(][0-9]+[.][ 0-9]+[)]", r" ", newline)

        # Remove sections "NNNN.MMM and NNNN.MMM"
        newline = re.sub(r"[0-9]+[.][0-9]+[,]? and [0-9]+[.][0-9]+",
                         r" ", newline)

        # Remove sections "NNNN.MMM,"
        newline = re.sub(r"[0-9]+[.][0-9]+\s*[,]", r" ", newline)

        # Ordered lists are changed from "N." to "(N)"
        newline = re.sub(r"[.]\s+([0-9]{1,2})[.]\s", r". (\1) ", newline)

        # Change "sections and sections" to just "sections"
        newline = re.sub(r"ection[s]?\s*and\s*[Ss]ection[s]?",
                         r"ections", newline)

        # remove all whitespace before certain punctuation marks
        newline = re.sub(r"\s+[,;]", "\1", newline)

        # shrink multiple spaces to a single space for readability
        newline = re.sub(r"\s+", " ", newline)

        return newline

    @staticmethod
    def merge_sentences(a_list):
        """ Merge sentences into a single line for IBM Watson NLU """

        if a_list:
            b_list = [""]
        merges = 0
        nextmerge = True
        first = True

        for a_line in a_list:
            merge = False
            sentence = a_line.strip()
            if first:
                if sentence == "":
                    merge = True
                if len(sentence) > 0 and " " not in sentence:
                    merge = True
                first = False

            if merge:
                b_list[-1] += sentence
                merges += 1
                nextmerge = True
            elif nextmerge:
                b_list[-1] += sentence
                nextmerge = False
            else:
                b_list.append(sentence)

        if merges > 0:
            logger.debug(f"Merges: {merges}")
        return b_list, merges

    def header_file_name(self, filename):
        """ Add filename to the header """

        self.add_text("_FILE_ "+filename)
        return self

    def header_hash_code(self, hashcode):
        """ Add hashcode to header """

        self.add_text(" _HASHCODE_ "+hashcode)
        return self

    def header_doc_date(self, docdate):
        """ Add document date to header.  """

        self.add_text(" _DOCDATE_ "+docdate)
        return self

    def header_bill_id(self, bill_id):
        """ Add the Legiscan bill_id to the header """

        self.add_text(" _BILLID_ {}".format(bill_id))
        return self

    def header_cite_url(self, cite_url):
        """ Add citation URL to state_link or Legiscan.com website """

        self.add_text(" _CITE_ "+cite_url)
        return self

    def header_title(self, title):
        """ Add title to the header """

        self.add_text(" _TITLE_ "+title)
        return self

    def header_summary(self, summary):
        """ Add summar to the header """

        self.add_text(" _SUMMARY_ "+summary)
        return self

    def header_end(self):
        """ Terminate header so that you can start adding text """

        self.add_text(' _TEXT_ ')
        return self

    @staticmethod
    def join_lines(lines):
        """ Join the lines into a single line """

        newlines = lines.splitlines()
        line = ' '.join(newlines)
        return line

    @staticmethod
    def parse_header(text):
        """ Parse headers at the beginning of text file """

        header, sections = {}, []
        # import pdb; pdb.set_trace()
        newline = Oneline.join_lines(text)

        if "_TEXT_" in newline:
            sections = newline.split('_TEXT_')
            logger.debug(f"Parsing: {newline[:80]}")
        else:
            logger.warning(f"Headers not found in text file. {newline[:80]}")

        if len(sections) == 2:
            head_text = sections[0] + " _TEXT_"
            mop = FILE_REGEX.search(head_text)
            if mop:
                header['FILE'] = mop.group(1).strip()

            mop = DOCDATE_REGEX.search(head_text)
            if mop:
                header['DOCDATE'] = mop.group(1).strip()

            mop = HASHCODE_REGEX.search(head_text)
            if mop:
                header['HASHCODE'] = mop.group(1).strip()

            mop = BILLID_REGEX.search(head_text)
            if mop:
                header['BILLID'] = mop.group(1).strip()

            mop = CITE_REGEX.search(head_text)
            if mop:
                header['CITE'] = mop.group(1).strip()

            mop = TITLE_REGEX.search(head_text)
            if mop:
                header['TITLE'] = mop.group(1).strip()

            mop = SUMMARY_REGEX.search(head_text)
            if mop:
                header['SUMMARY'] = mop.group(1).strip()
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

    print(" ")
    print("================TEST 1 =====================")
    print(" ")
    PARAGRAPH = ("_FILE_ OH-SB66-1422-Y2017.pdf  _BILLID_ 968725  "
                 "_DOCDATE_ 2018-07-09  "
                 "_HASHCODE_ 758a357a208dd4385fe1c7cc93c6fb7e  "
                 "_CITE_ http://search-prod.lis.state.oh.us/968725.pdf "
                 "_TITLE_ Modify Criminal Sentencing and Corrections Law  "
                 "_SUMMARY_ To authorize state-owNed real estate.\n "
                 "This triumph attests to the resolve of these people.\n "
                 "_TEXT_ This is the start of the bill.")
    head = Oneline.parse_header(PARAGRAPH)
    print(head)

    print(" ")
    print("================TEST 2 =====================")
    print(" ")
    P2 = ("_FILE_ OH-SR99-1646-Y2019.pdf  _BILLID_ 1246079  _DOCDATE_ "
          "2019-03-28  _HASHCODE_ 674ea39d3574fd92208202b492dfc43b  _CITE_ "
          "http://search-prod.lis.state.oh.us/solarapi/v1/general_assembly"
          "_133/resolutions/sr99/AS/01?format=pdf  _TITLE_ Honoring Seth "
          "Shumate as the 2019 Division I State Wrestling Champion in the "
          "195-Pound Weight Class.\n_SUMMARY_ Honoring Seth Shumate as the "
          "2019 Division I State Wrestling \nChampion in the 195-pound weight "
          "class. _TEXT_  As Adopted by the Senate 133rd General Assembly "
          "Regular Session 2019-2020 SR99 Senator Kunze A")

    head = Oneline.parse_header(P2)
    print(head)

    print(" ")

    # p3 = Oneline()
    # p3.add_text("This is a test.\nThese are normal sentences.\n"
    #             "The algorithm should put each on a separate line.\n"
    #             "there should be five lines.\nThis is the last one.")
    # p3.split_sentences()
    # print("==["+p3.oneline+"]==")

    # p4 = Oneline()
    # p4.add_text("This is a test.\n\n\n\nSec.\n\n3.\n\n\n5.\n\n\n"
    #             "has been withdrawn.")
    # p4.split_sentences()
    # print("==["+p4.oneline+"]==")

    T1 = ("H. R. No. 77,    H. B. 33, S. B. 88, sections 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44 and sections 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44; 131st G.A 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44;   132nd G.A., "
          "133rd G.A., 134th G.A. Am. Sub. Sec. 3   Sub. 4  SEC. 5")

    print(T1)

    print(Oneline.common_acronyms(T1))

    with open("NLTK-sample.txt", "r") as in_file:
        textdata = in_file.read()
        p5 = Oneline()
        p5.add_text(textdata)
        # import pdb; pdb.set_trace()
        p5.split_sentences()
        with open("NLTK-sample.out", "w") as out_file:
            out_file.write(p5.oneline)
        print("NLTK-sample.out created")

    print('Congratulations')
