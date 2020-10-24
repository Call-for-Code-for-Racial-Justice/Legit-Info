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
import tempfile
import zipfile
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand

from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.ShowProgress import ShowProgress
from cfc_app.PDFtoTEXT import PDFtoTEXT
from cfc_app.models import Location
from cfc_app.LegiscanAPI import LegiscanAPI, LegiscanError
from cfc_app.Oneline import Oneline
from cfc_app.DataBundle import DataBundle


PARSER = "lxml"
TITLE_LIMIT = 200
SUMMARY_LIMIT = 1000

# Put the original file name, doc date, title and summary ahead of text
HeadForm = "{} {} _TITLE_ {} _SUMMARY_ {} _TEXT_"

billRegex = re.compile(r"^(\w\w)/\d\d\d\d-(\d\d\d\d).*/bill/(\w*).json$")
dslRegex = re.compile(r"^(\w\w)-(\d\d\d\d)-(\w*).json$")
keyForm = "{}-{}-Y{}"
nameForm = "{}.{}"


class Command(BaseCommand):
    help = ("For each state, scan the associated SS-NNNN-Dataset.json "
            "and SS-NNNN-Master.json files, fetching the legislation "
            "as either HTML or PDF file, and extract to TEXT.  Both the "
            "original (HTML/PDF) and the extracted TEXT file are stored "
            "in File/Object Storage.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = LegiscanAPI()

        self.use_api = False
        self.skip = False
        self.sessions = 1
        self.session_id = None
        self.limit = 10
        self.state_count = 0
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--sessions", type=int, default=self.limit,
                            help="Number of legislative sessions per state")
        parser.add_argument("--session_id", help="Process this session only")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Number of bills to extract per state")
        parser.add_argument("--skip", action="store_true",
                            help="Skip files already processed")

        return None

    def handle(self, *args, **options):

        if options['sessions']:
            self.sessions = options['sessions']

        if options['state']:
            self.state = options['state']

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.use_api = True

        if options['skip']:
            self.skip = True

        if options['session_id']:
            self.session_id = options['session_id']
            self.state = None

        # Use the Django "Location" database to get list of states.

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE

            # If we are only processing one state, and this is
            # not it, skip it.
            if self.state and (state != self.state):
                continue

            print('Processing state: ', state)
            self.state_count = 0
            hlist = self.fob.list_items(prefix=state, suffix='.json')

            sesh_dict = []
            for json_name in hlist:
                mo = dslRegex.search(json_name)
                if mo:
                    state = mo.group(1)
                    session_id = mo.group(2)

                    # If you are only doing one session_id, and this one
                    # isn't it, continue to the next session_id
                    if self.session_id and (session_id != self.session_id):
                        continue

                    # Insert in front of list to put most recent years first
                    if session_id not in sesh_dict:
                        sesh_dict.insert(0, session_id)

            # Loop through the sessions found, most recent first, until
            # number of sessions to process are met
            count = 0
            for session_id in sesh_dict:
                if self.limit > 0 and self.state_count >= self.limit:
                    break
                self.process_json(state, session_id)
                count += 1
                if count >= self.sessions:
                    break

        return None

    def process_json(self, state, session_id):
        """ Process SS-NNNN-Dataset.json and SS-NNNN-Master.json """
        # import pdb; pdb.set_trace()

        dsl_name = '{}-{}-Dataset.json'.format(state, session_id)
        json_str = self.fob.download_text(dsl_name)
        zip_name = dsl_name.replace('.json', '.zip')

        print('Checking: ', dsl_name)
        dot = ShowProgress()

        # If the ZIP file already exists, use it, otherwise create it.
        if self.fob.item_exists(zip_name):
            msg_bytes = self.fob.download_binary(zip_name)
        else:
            package = json.loads(json_str)
            if package['status'] == 'OK':
                dataset = package['dataset']
                mimedata = dataset['zip'].encode('UTF-8')
                msg_bytes = base64.b64decode(mimedata)
                self.fob.upload_binary(msg_bytes, zip_name)

        #import pdb; pdb.set_trace()

        with tempfile.NamedTemporaryFile(suffix='.zip',prefix='tmp-',
                                         delete=True) as temp_zip:
            temp_zip.write(msg_bytes)
            temp_zip.seek(0)

            with zipfile.ZipFile(temp_zip.name, 'r') as zf:
                namelist = zf.namelist()
                for path in namelist:
                    if self.limit > 0 and self.state_count >= self.limit:
                        break
                    mo = billRegex.search(path)
                    if mo:
                        dot.show()
                        json_data = zf.read(path).decode('UTF-8', 
                                                         errors='ignore')
                        self.state_count += self.process_source(mo, json_data)

        dot.end()
        return None

    def process_source(self, mo, json_data):
        bill_state = mo.group(1)
        bill_year = mo.group(2)
        bill_number = mo.group(3)
        bill_json = json.loads(json_data)
        bill_detail = bill_json['bill']
        texts = bill_detail['texts']
        chosen = self.latest_text(texts)
        extension = self.determine_extension(chosen['mime'])
        key = keyForm.format(bill_state, bill_number, bill_year)
        text_name = nameForm.format(key, "txt")

        if self.skip and self.fob.item_exists(text_name):
            print('File exists, skipping: ', text_name)
            processed = 0
        else:
            self.process_bill(key, extension, bill_detail, chosen)
            processed = 1
        return processed

    def process_bill(self, key, extension, bill_detail, chosen):
        bill_name = nameForm.format(key, extension)
        title = bill_detail['title']
        summary = bill_detail['description']

        params = {}
        # import pdb; pdb.set_trace()
        if extension == 'html':
            html_bundle = DataBundle(bill_name)
            response = html_bundle.make_request(chosen['state_link'], params)
            result = html_bundle.load_response(response)
            if result:
                textdata = html_bundle.text
                
                self.fob.upload_text(textdata, bill_name)
                self.process_html(key, chosen['date'], bill_detail, textdata)

        elif extension == 'pdf':
            pdf_bundle = DataBundle(bill_name)
            # import pdb; pdb.set_trace()
            response = pdf_bundle.make_request(chosen['state_link'], params)
            result = pdf_bundle.load_response(response)
            if result:
                bindata = pdf_bundle.content
                self.fob.upload_binary(bindata, bill_name)
                self.process_pdf(key, chosen['date'], bill_detail, bindata)

        return

    def process_html(self, key, docdate, bill_detail, billtext):
        bill_name = nameForm.format(key, 'html')
        text_name = nameForm.format(key, 'txt')

        text_line = Oneline()
        title, summary = bill_detail['title'], bill_detail['description']
        text_line.add_text(HeadForm.format(bill_name, docdate, title, summary))
        self.parse_html(billtext, text_line)
        text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(textname)
        print('Writing: ', textname)
        return self

    def process_pdf(self, key, docdate, bill_detail, msg_bytes):

        imput_str = ""
        with tempfile.NamedTemporaryFile(suffix='.pdf',prefix='tmp-',
                                         delete=True) as temp_pdf:
            temp_pdf.write(msg_bytes)
            temp_pdf.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.txt',prefix='tmp-',
                                         delete=True) as temp_out:
                PDFtoTEXT(temp_pdf.name, temp_out.name)
                temp_out.seek(0)
                imput_str = temp_out.read().decode('UTF-8')

        bill_name = nameForm.format(key, 'pdf')
        title, summary = bill_detail['title'], bill_detail['description']
        header = HeadForm.format(bill_name, docdate, title, summary)
        
        text_name = nameForm.format(key, 'txt')
        text_line = Oneline()
        text_line.add_text(header)
        if input_str:
            self.parse_intermediate(input_str, text_line)
            text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(textname)
        print('Writing: ', textname)
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
            extension == 'html'  # Assume html for Arizona
            billtext = ''
            billname = '{}.{}'.format(key, extension)
            if self.fob.item_exists(billname):
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
            if self.fob.item_exists(billname):
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



    def parse_intermediate(self, input_string, output_line):
        lines = input_string.splitlines()
        for line in lines:
            newline = line.replace('B I L L', 'BILL')
            newline = newline.strip()
            # Remove lines that only contain blanks or line numbers only
            if newline != '' and not newline.isdigit():
                output_line.add_text(newline)
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

    def source_name(self, state, bill_number, bill_year, mime_type):
        extension = self.determine_extension(mime_type)
        item_name = nameForm.format(state, bill_number, bill_year, extension)
        return item_name

    def latest_text(self, texts):
        LastDate = "0000-00-00"
        LastDocid = 0
        LastEntry = None
        for entry in texts:
            this_date = entry['date']
            this_docid = entry['doc_id']
            if (this_date > LastDate or
               (this_date == LastDate and this_docid > LastDocid)):
                LastDate = this_date
                LastDocid = this_docid
                LastEntry = entry

        return LastEntry
