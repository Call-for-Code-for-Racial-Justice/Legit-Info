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
from urllib.parse import urlparse

# Django and other third-party imports
from django.conf import settings
logger = logging.getLogger(__name__)

def date_type(date_string):
    """ Convert "YYYY-MM-DD" string to datetime.date format """
    date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
    return date_value

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
        shrink_line(newline, charlimit)

    # Capitalize the (possibly new) first word in the sentence.
    newline = newline[0].upper() + newline[1:]
    return newline

def shrink_line(line, charlimit):
    """ if chopping a line from the front, find next full word """

    newline = re.sub(r'^\W*\w*\W*', '', line[-charlimit:])
    newline = re.sub(r'^and ', '', newline)
    newline = newline[0].upper() + newline[1:]
    return newline


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
            
            self.title = form_sentence(jsondet['title'], 200)
            self.summary = form_sentence(jsondet['summary'], 1000)
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




# end of module
