# Python Code
# scan_json.py -- Scan JSON retrieved by get_api_data.
# By Tony Pearson, IBM, 2020
#
# This is intended as a background task
#
# You can invoke this in either "on demand" or as part of a "cron" job
#
# On Demand:
# [...] $ pipenv shell
# (cfc) $ ./stage1 scan_json --api --state AZ --limit 10
#
# Cron Job:
# /home/yourname/Develop/legit-info/cron1 scan_json --api --limit 10
#
# The Legiscan.com API only allows 30,000 fetches per 30-day period, and
# each legislation requires at least 2 fetches, so use the --limit keyword
#
# If you leave out the --api, the Legiscan.com API will not be invoked,
# this is useful to process HTML and PDF files already fetched from API.
#
# Debug with:   import pdb; pdb.set_trace()

import base64
import json
import os
import re
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand

from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.ShowProgress import ShowProgress
from cfc_app.PDFtoTEXT import PDFtoTEXT
from cfc_app.models import Location
from cfc_app.Legiscan_API import Legiscan_API, LegiscanError
from cfc_app.Oneline import Oneline


PARSER = "lxml"
TITLE_LIMIT = 200
SUMMARY_LIMIT = 1000

# Put the original file name, doc date, title and summary ahead of text
HeadForm = "{} {} _TITLE_ {} _SUMMARY_ {} _TEXT_"


class Command(BaseCommand):
    help = 'For each state, scan the associated NN.json file, fetching '
    help += 'legislation from Legiscan.API as either HTML or PDF file, '
    help += 'and extract to TEXT.  Both the original (HTML/PDF) and the '
    help += 'extracted TEXT file are stored in File/Object Storage.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = Legiscan_API()

        self.use_api = False
        self.skip = False
        self.limit = 10
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=10,
                            help="Limit number of entries to detail")
        parser.add_argument("--skip", action="store_true",
                            help="Skip files already processed")

        return None

    def handle(self, *args, **options):

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.use_api = True

        if options['skip']:
            self.skip = True

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE

            # If we are only processing one state, and this is
            # not it, skip it.
            if options['state'] and state != options['state']:
                continue
            json_handle = '{}.json'.format(state)
            self.process_json(state, json_handle)
        return None

    def process_json(self, state, json_handle):
        """ Process NN.json for this state """
        # import pdb; pdb.set_trace()
        json_str = self.fob.download_text(json_handle)
        bills = json.loads(json_str)

        dot = ShowProgress()
        count = 0
        for index in bills:

            # import pdb; pdb.set_trace()
            dot.show()
            bill = bills[index]

            key = "{}-{}".format(state, bill['bill_number'])
            document_date = ''
            if 'doc_date' in bill:
                document_date = bill['doc_date']
                if len(key) < 15:
                    key += '-Y' + bill['doc_date'][:4]
                else:
                    key += '-Y' + bill['doc_date'][2:4]

            title = self.form_sentence(bill['title'], TITLE_LIMIT)
            summary = self.form_sentence(bill['summary'], SUMMARY_LIMIT)

            # If the text file already exists, honor the --skip flag
            textname = '{}.{}'.format(key, 'txt')
            if self.skip and self.fob.handle_exists(textname):
                print('File exists, skipping: ', textname)
                continue

            # Don't invoke Legiscan.com API unless --api specified
            if self.use_api and self.leg.api_ok:
                extension, msg_bytes = self.fetch_bill(bill, key)

            # Otherwise, download the HTML/PDF file
            else:
                extension, msg_bytes = self.read_from_fob(key)

            if extension == 'html':
                self.process_html(key, document_date,
                                  title, summary, msg_bytes)
            elif extension == 'pdf':
                self.process_pdf(key, document_date,
                                 title, summary, msg_bytes)

            count += 1
            if self.limit > 0 and count >= self.limit:
                break

            dot.end()
        return self

    def form_sentence(self, line, charlimit):
        newline = self.remove_section_numbers(line)

        # Remove trailing spaces, and add period at end of sentence.
        newline = newline.strip()
        if not newline.endswith('.'):
            newline = newline + '.'

        # If the line is longer than the limit, keep the number
        # of characters from the end of the sentence.  If this
        # results a word being chopped in half, remove the half-word

        if len(newline) > charlimit:
            self.shrink_line(newline, charlimit)

        # Capitalize the (possibly new) first word in the sentence.
        newline = newline[0].upper() + newline[1:]
        return newline

    def fetch_bill(self, bill, key):
        extension, msg_bytes = '', b''
        docID = bill['doc_id']
        response = ''
        if self.use_api and self.leg.api_ok:
            try:
                response = self.leg.getBillText(docID)
            except Exception as e:
                self.leg.api_ok = False
                print('Error: {}'.format(e))
                raise LegiscanError

        if response != '':
            mime_type = response['mime_type']
            extension = self.determine_extension(mime_type)

            mimedata = response['doc'].encode('UTF-8')
            msg_bytes = base64.b64decode(mimedata)

            billname = '{}.{}'.format(key, extension)
            print('Getting from Legiscan: ', billname)

        if extension == 'html':
            billtext = msg_bytes.decode('UTF-8', errors='ignore')
            self.fob.upload_text(billname, billtext)
        elif extension == 'pdf':
            self.fob.upload_binary(billname, msg_bytes)

        return extension, msg_bytes

    def read_from_fob(self, key):
        extension, msg_bytes = '', b''
        state = key[:2]
        if state == 'AZ':
            extension = 'html'  # Assume html for Arizona
            billtext = ''
            billname = '{}.{}'.format(key, extension)
            if self.fob.handle_exists(billname):
                billtext = self.fob.download_text(billname)
                msg_bytes = billtext.encode('UTF-8')
            if billtext == '':
                print('File not found: ', billname)
                extension = ''
            else:
                print('Reading: ', billname)

        elif state == 'OH':
            extension = 'pdf'   # Assume html for Ohio
            billname = '{}.{}'.format(key, extension)
            if self.fob.handle_exists(billname):
                msg_bytes = self.fob.download_binary(billname)
            if msg_bytes == b'':
                print('File not found: ', billname)
                extension = ''
            else:
                print('Reading: ', billname)
        return extension, msg_bytes

    def parse_html(self, in_line, out_line):
        soup = BeautifulSoup(in_line, PARSER)
        title = soup.find('title')
        if title:
            out_line.add_text(title.string)

        sections = soup.findAll("span", {"class": "SECHEAD"})
        for section in sections:
            rawtext = section.string
            if rawtext:
                lines = rawtext.splitlines()
                header = " ".join(lines)
                out_line.add_text(header)

        paragraphs = soup.findAll("p")
        for paragraph in paragraphs:
            pg = paragraph.string
            if pg:
                out_line.add_text(pg)

        return self

    def process_html(self, key, docdate, title, summary, billtext):
        billname = '{}.{}'.format(key, 'html')
        textname = '{}.{}'.format(key, 'txt')

        text_line = Oneline()
        text_line.add_text(HeadForm.format(billname, docdate, title, summary))
        self.parse_html(billtext, text_line)
        text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(textname)
        print('Writing: ', textname)
        return self

    def parse_intermediate(self, input_string, output_line):
        lines = input_string.splitlines()
        for line in lines:
            newline = line.replace('B I L L', 'BILL')
            newline = newline.strip()
            # Remove lines that only contain blanks or line numbers only
            if newline != '' and not newline.isdigit():
                output_line.add_text(newline)
        return self

    def process_pdf(self, key, docdate, title, summary, msg_bytes):
        bill_path = os.path.join(settings.SOURCE_ROOT, "scan_json.pdf")
        with open(bill_path, "wb") as outfile:
            outfile.write(msg_bytes)
            intermediate = "intermediate.file"
            PDFtoTEXT(bill_path, intermediate)

        billname = '{}.{}'.format(key, 'pdf')
        textname = '{}.{}'.format(key, 'txt')
        text_line = Oneline()
        text_line.add_text(HeadForm.format(billname, docdate, title, summary))
        with open(intermediate, "r") as infile:
            input_str = infile.read()
            self.parse_intermediate(input_str, text_line)
        text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(textname)
        print('Writing: ', textname)
        return self

    def remove_section_numbers(self, line):
        newline = re.sub(r'and [-0-9]+[.][0-9]+\b\s*', '', line)
        newline = re.sub(r'\([-0-9]+[.][0-9]+\)[,]?\s*', '', newline)
        newline = re.sub(r'\b[-0-9]+[.][0-9]+\b[,]?\s*', '', newline)
        newline = re.sub(
            r'section[s]? and section[s]?\s*', 'sections', newline)
        newline = re.sub(r'section[s]?\s*;\s*', '; ', newline)
        newline = re.sub(r'amend; to amend,\s*', 'amend ', newline)
        newline = newline.replace("'", "-").replace('"', '_')
        newline = newline.replace(r'\x91', '')

        # Collapse "H. B. No. 43" to just "HB43", for example
        newline = newline.replace(r'H. B. No. ', 'HB')
        newline = newline.replace(r'S. B. No. ', 'SB')
        newline = newline.replace(r'H. R. No. ', 'HR')
        newline = newline.replace(r'S. R. No. ', 'SR')
        newline = newline.replace(r'C. R. No. ', 'CR')
        newline = newline.replace(r'J. R. No. ', 'JR')
        return newline

    def shrink_line(self, line, charlimit):
        newline = re.sub(r'^\W*\w*\W*', '', line[-charlimit:])
        newline = re.sub(r'^and ', '', newline)
        newline = newline[0].upper() + newline[1:]
        return newline

    def determine_extension(self, mime_type):
        extension = 'unk'
        if mime_type == 'text/html':
            extension = 'html'
        elif mime_type == 'application/pdf':
            extension = 'pdf'
        elif mime_type == 'application/doc':
            extension = 'doc'

        return extension
