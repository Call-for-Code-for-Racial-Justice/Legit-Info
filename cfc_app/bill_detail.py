#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bill details for extract_files

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""
# System imports
import datetime as DT
import logging
import re
import sys
from urllib.parse import urlparse

# Django and other third-party imports
from django.conf import settings

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

MAX_TITLE = 200
MAX_SUMMARY = 1000


def date_type(date_string):
    """ Convert "YYYY-MM-DD" string to datetime.date format """
    date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
    return date_value


class BillDetail():
    """ Bill details for extract_files """

    def __init__(self, jsondet=None):
        self.bill_id = None
        self.bill_number = None
        self.cite_url = None
        self.doc_date = None
        self.doc_size = None
        self.extension = None
        self.key = None
        self.bill_name = None
        self.hashcode = None
        self.session_id = None
        self.state = None
        self.state_link = None
        self.summary = None
        self.texts = None
        self.title = None
        self.url = None
        self.doc_id = None

        if jsondet:
            self.bill_id = jsondet['bill_id']

            self.title = BillDetail.form_sentence(jsondet['title'], MAX_TITLE)
            self.summary = BillDetail.form_sentence(jsondet['description'],
                                                    MAX_SUMMARY)
            if self.title == self.summary:
                self.summary = ""
            self.hashcode = jsondet['change_hash']
            self.session_id = jsondet['session']['session_id']
            self.state = jsondet['state']
            self.bill_number = jsondet['bill_number']
            self.texts = jsondet['texts']
        return None

    def choose_document(self, chosen):
        """ Update bill_detail with chosen document """
        logger.debug(f"54: {chosen}")
        self.extension = BillDetail.determine_extension(chosen['mime'])
        self.doc_id = chosen['doc_id']
        self.doc_date = chosen['date']
        self.doc_size = chosen['text_size']
        self.url = chosen['url']
        self.state_link = chosen['state_link']
        return None

    def parse_url(self):
        """ parse state_link into baseurl and params """

        source = urlparse(self.state_link)
        self.cite_url = self.state_link

        params = {}
        if source.query:
            querylist = source.query.split('&')
            for querystring in querylist:
                qfragments = querystring.split('=')
                if len(qfragments) == 2:
                    qkey, qvalue = qfragments
                    params[qkey] = qvalue

        if source.scheme:
            baseurl = f"{source.scheme}://{source.netloc}{source.path}"
        else:
            baseurl = f"http://{source.netloc}{source.path}"

        return baseurl, params

    @staticmethod
    def determine_extension(mime_type):
        """ Determine extension to use for each mime_type """

        extension = 'unk'
        if mime_type == 'text/html':
            extension = 'html'
        elif mime_type == 'application/pdf':
            extension = 'pdf'
        elif mime_type == 'application/doc':
            extension = 'doc'
        return extension

    def latest_text(self):
        """ If legislation has two or more documents, pick the latest one """

        last_date = settings.LONG_AGO

        last_docid = 0
        last_entry = None
        earliest_year = 2999
        for entry in self.texts:
            this_date = date_type(entry['date'])
            this_docid = entry['doc_id']
            if this_date.year < earliest_year:
                earliest_year = this_date.year
            if (this_date > last_date or
                    (this_date == last_date and this_docid > last_docid)):
                last_date = this_date
                last_docid = this_docid
                last_entry = entry

        return earliest_year, last_entry

    @staticmethod
    def form_sentence(line, charlimit):
        """ Reduce title/summary to fit within character limits """

        # Remove trailing spaces, and add period at end of sentence.
        newline = line.strip()
        if not newline.endswith('.'):
            newline = newline + '.'

        # If the line is longer than the limit, keep the number
        # of characters from the end of the sentence.  If this
        # results a word being chopped in half, remove the half-word

        if len(newline) > charlimit:
            newline = BillDetail.shrink_line(newline, charlimit)

        # Capitalize the (possibly new) first word in the sentence.
        newline = newline[0].upper() + newline[1:]
        return newline

    @staticmethod
    def shrink_line(line, charlimit):
        """ if chopping a line from the front, find next full word """

        keep, extra = "", ""

        lines = line.split('. ')
        keep = lines[0] + "."
        if len(keep) > charlimit:
            newline = keep[-charlimit:]
            newline = re.sub(r'^\W*\w*\W*', '', newline)
            newline = re.sub(r'^and ', '', newline)
            newline = newline[0].upper() + newline[1:]
            keep = newline

        for stem in reversed(lines[1:]):
            if (len(keep)+len(extra)) < (charlimit - len(stem) - 2):
                if stem.strip().endswith("."):
                    extra = stem + extra
                else:
                    extra = stem + ". " + extra
            else:
                break

        return keep + extra


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    stm = ("For the People Act of 2019 This bill addresses voter access, "
           "election integrity, election security, political spending, and "
           "ethics for the three branches of government. Specifically, the "
           "bill expands voter registration and voting access and limits "
           "removing voters from voter rolls. The bill provides for states to "
           "establish independent, nonpartisan redistricting commissions. The "
           "bill also sets forth provisions related to election security, "
           "including sharing intelligence information with state election "
           "officials, protecting the security of the voter rolls, supporting "
           "states in securing their election systems, developing a national "
           "strategy to protect the security and integrity of U.S. democratic "
           "institutions, establishing in the legislative branch the National "
           "Commission to Protect United States Democratic Institutions, and "
           "other provisions to improve the cybersecurity of election "
           "systems. This bill addresses campaign spending, including by "
           "expanding the ban on foreign nationals contributing to or "
           "spending on elections; expanding disclosure rules pertaining to "
           "organizations spending money during elections, campaign "
           "advertisements, and online platforms; and revising disclaimer "
           "requirements for political advertising. This bill establishes an "
           "alternative campaign funding system for certain federal offices. "
           "The system involves federal matching of small contributions for "
           "qualified candidates. This bill sets forth provisions related "
           "to ethics in all three branches of government. Specifically, "
           "the bill requires a code of ethics for federal judges and "
           "justices, prohibits Members of the House from serving on the "
           "board of a for-profit entity, expands enforcement of regulations "
           "governing foreign agents, and establishes additional "
           "conflict-of-interest and ethics provisions for federal employees "
           "and the White House. The bill also requires candidates for "
           "President and Vice President to submit 10 years of tax returns.")

    x = BillDetail.form_sentence(stm, MAX_TITLE)
    print(x, len(x))
    print("---------------------------------------")
    y = BillDetail.form_sentence(stm, MAX_SUMMARY)
    print(y, len(y))
    print("---------------------------------------")
    z = BillDetail.form_sentence(stm, 100)
    print(z, len(z))


# end of module
