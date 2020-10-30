#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to create file as a single text line.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import sys
import re
import nltk
import logging
logger = logging.getLogger(__name__)

# Debug with:  import pdb; pdb.set_trace()


class OnelineError(RuntimeError):
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
        newline = line.replace('\u2011', '-').replace('\u2013', '-')
        newline = newline.replace('\u2019', '-')
        newlines = newline.splitlines()
        newline2 = ' '.join(newlines)
        self.oneline += newline2 + ' '
        return self

    def split_sentences(self):
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

            header = "{} _SUMMARY {} _TEXT_ \n".format(front, summary)
            newline = Oneline.common_acronyms(sections[1])

        a_list = nltk.tokenize.sent_tokenize(newline)
        c_list, merges = Oneline.merge_sentences(a_list)
        a_list = c_list

        logger.debug("61:Merges={} Lines={}".format(merges, len(a_list)))

        self.oneline = header + '\n'.join(a_list)
        return self

    def common_acronyms(line):
        newline = line.replace(r'\x91', '')
        newline = re.sub(r"H.\s*B.\s*No.\s*(\d)", r"HB\1", newline)
        newline = re.sub(r"S.\s*B.\s*No.\s*(\d)", r"SB\1", newline)
        newline = re.sub(r"H.\s*R.\s*No.\s*(\d)", r"HR\1", newline)
        newline = re.sub(r"S.\s*R.\s*No.\s*(\d)", r"SR\1", newline)
        newline = re.sub(r"C.\s*R.\s*No.\s*(\d)", r"CR\1", newline)
        newline = re.sub(r"J.\s*R.\s*No.\s*(\d)", r"JR\1", newline)

        newline = re.sub(r"H.\s*B.\s*(\d)", r"HB\1", newline)
        newline = re.sub(r"S.\s*B.\s*(\d)", r"SB\1", newline)
        newline = re.sub(r"Am.\sSub.", r"Am-Sub", newline)
        newline = re.sub(r"(st|nd|rd|th) G.A.", r"\1-GA ", newline)
        newline = re.sub(r"(Sec|Sub|SEC)[.]\s*([0-9]+)", r" \1#\2 ", newline)
        newline = re.sub(r"[(][0-9]+[.][ 0-9]+[)]", r" ", newline)
        newline = re.sub(r"[0-9]+[.][0-9]+[,]? and [0-9]+[.][0-9]+",
                         r" ", newline)
        newline = re.sub(r"[0-9]+[.][0-9]+\s*[,]", r" ", newline)
        newline = re.sub(r"ection[s]?\s*and\s*[Ss]ection[s]?",
                         r"ections", newline)
        newline = re.sub(r"\s+;", ";", newline)
        newline = re.sub(r"\s+,", ",", newline)
        newline = re.sub(r"\s+", " ", newline)

        return newline

    def merge_sentences(a_list):
        if a_list:
            b_list = [""]
        merges = 0
        nextmerge = True

        for n in range(len(a_list)):
            merge = False
            sentence = a_list[n].strip()
            if n > 0:
                if sentence == "":
                    merge = True
                if len(sentence) > 0 and " " not in sentence:
                    merge = True

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
            logger.debug("Merges: {}".format(merges))
        return b_list, merges

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

    def join_lines(lines):
        newlines = lines.splitlines()
        line = ' '.join(newlines)
        return line

    def parse_header(text):
        """ Parse headers at the beginning of text file """

        FILE_REGEX = re.compile(r"_FILE_\s*(.*?) _")
        DOCDATE_REGEX = re.compile(r"_DOCDATE_\s*(.*?) _")
        HASHCODE_REGEX = re.compile(r"_HASHCODE_\s*(.*?) _")
        BILLID_REGEX = re.compile(r"_BILLID_\s*(.*?) _")
        CITE_REGEX = re.compile(r"_CITE_\s*(.*?) _")
        TITLE_REGEX = re.compile(r"_TITLE_\s*(.*?) _")
        SUMMARY_REGEX = re.compile(r"_SUMMARY_\s*(.*?) _")

        header, sections = {}, []
        # import pdb; pdb.set_trace()
        newline = Oneline.join_lines(text)

        if "_TEXT_" in newline:
            sections = newline.split('_TEXT_')
            logger.debug("Parsing: "+newline[:80])
        else:
            warn_msg = "Headers not found in text file. {}"
            logger.warning(warn_msg.format(newline[:80]))

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

    print(" ")
    print("================TEST 1 =====================")
    print(" ")
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

    print(" ")
    print("================TEST 2 =====================")
    print(" ")
    p2 = ("_FILE_ OH-SR99-1646-Y2019.pdf  _BILLID_ 1246079  _DOCDATE_ "
          "2019-03-28  _HASHCODE_ 674ea39d3574fd92208202b492dfc43b  _CITE_ "
          "http://search-prod.lis.state.oh.us/solarapi/v1/general_assembly"
          "_133/resolutions/sr99/AS/01?format=pdf  _TITLE_ Honoring Seth "
          "Shumate as the 2019 Division I State Wrestling Champion in the "
          "195-Pound Weight Class.\n_SUMMARY_ Honoring Seth Shumate as the "
          "2019 Division I State Wrestling \nChampion in the 195-pound weight "
          "class. _TEXT_  As Adopted by the Senate 133rd General Assembly "
          "Regular Session 2019-2020 SR99 Senator Kunze A")

    head = Oneline.parse_header(p2)
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

    t1 = ("H. R. No. 77,    H. B. 33, S. B. 88, sections 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44 and sections 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44; 131st G.A 999.99, 888.88, "
          "777.77 (654.32), 555.55, and 444.44;   132nd G.A., "
          "133rd G.A., 134th G.A. Am. Sub. Sec. 3   Sub. 4  SEC. 5")

    print(t1)

    print(Oneline.common_acronyms(t1))

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
