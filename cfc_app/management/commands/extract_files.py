# Python Code
# extract_files.py -- Extract text from HTML/PDF files
# By Tony Pearson, IBM, 2020
#
# This is intended as a background task
#
# You can invoke this in either "on demand" or as part of a "cron" job
#
# On Demand:
# [...] $ pipenv shell
# (cfc) $ ./stage1 extract_files --api --state AZ --limit 10
#
# Cron Job:
# /home/yourname/Develop/legit-info/cron1 extract_files --api --limit 10
#
# The Legiscan.com API only allows 30,000 fetches per 30-day period, so
# we will download HTML/PDF versions from each state's website instead.
# If that fails, we can then fetch from Legiscan API.
#
# If you leave out the --api, the Legiscan.com API will not be invoked.
#
# Debug with:   import pdb; pdb.set_trace()

import base64
import datetime as DT
import json
from random import randint
import os
import re
import tempfile
import zipfile
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand

from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.ShowProgress import ShowProgress
from cfc_app.PDFtoTEXT import PDFtoTEXT
from cfc_app.models import Law, Location, Hash
from cfc_app.LegiscanAPI import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.Oneline import Oneline
from cfc_app.DataBundle import DataBundle


PARSER = "lxml"
TITLE_LIMIT = 200
SUMMARY_LIMIT = 1000

# Put the original file name, doc date, title and summary ahead of text
HeadForm = "{} {} _TITLE_ {} _SUMMARY_ {} _TEXT_"

billRegex = re.compile(r"^([A-Z]{2})/\d\d\d\d-(\d\d\d\d).*/bill/(\w*).json$")
keyForm = "{}-{}-{}"
nameForm = "{}.{}"


class Command(BaseCommand):
    help = ("For each state, scan the associated CC-Dataset-NNNN.json "
            "fetching the legislation as either HTML or PDF file, and "
            "extract to TEXT.  Both the original (HTML/PDF) and the "
            "extracted TEXT file are stored in File/Object Storage, "
            "so that they can be compared by developers to validate "
            "the text analysis.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.leg = LegiscanAPI()

        self.api_limit = 0
        self.state = None
        self.session_id = None
        self.limit = 10
        self.skip = False
        self.rand_key = "tmp" + str(randint(1000, 9999))
        self.state_count = 0
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API, if needed")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--session_id", help="Process this session only")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Number of bills to extract per state")
        parser.add_argument("--skip", action="store_true",
                            help="Skip files already in File/Object storage")

        return None

    def handle(self, *args, **options):

        if options['state']:
            self.state = options['state']

        if options['limit']:
            self.limit = options['limit']

        if options['api']:
            self.api_limit = 10

        if options['skip']:
            self.skip = True

        if options['session_id']:
            self.session_id = options['session_id']
            self.state = None

        # Use the Django "Location" database to get list of locations
        # listed with valid (non-zero) Legiscan_id.  For example,
        # Legiscan_id=3 for Arizona, and Legiscan_id=35 for Ohio.

        locations = Location.objects.filter(legiscan_id__gt=0)

        for loc in locations:
            self.loc = loc
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            # If we are only processing one state, and this is
            # not it, continue to the next state.
            if self.state and (state != self.state):
                continue

            print('Processing: {} ({})'.format(loc.desc, state))
            self.state_count = 0
            found_list = self.fob.Dataset_items(state)

            sessions = []
            found_list.sort(reverse=True)
            for json_name in found_list:
                mo = self.fob.Dataset_search(json_name)
                if mo:
                    state = mo.group(1)
                    session_id = mo.group(2)

                    # If you are only doing one session_id, and this one
                    # isn't it, continue to the next session_id.
                    if self.session_id and (session_id != self.session_id):
                        continue

                    # Add session_id to list of sessions found.
                    if session_id not in sessions:
                        sessions.append([session_id, json_name])

            # Loop through the sessions found, most recent first, until
            # the limit of bills to process is reached for this state.
            sessions.sort(reverse=True)
            for session_detail in sessions:
                if self.limit > 0 and self.state_count >= self.limit:
                    break
                session_id, json_name = session_detail
                self.process_json(state, session_id, json_name)

        return None

    def process_json(self, state, session_id, json_name):
        """ Process CC-Dataset-NNNN.json file """

        json_str = self.fob.download_text(json_name)

        print('Checking: ', json_name)
        dot = ShowProgress()

        # If the ZIP file already exists, use it, otherwise create it.
        zip_name = json_name.replace('.json', '.zip')
        if self.fob.item_exists(zip_name):
            msg_bytes = self.fob.download_binary(zip_name)
        else:
            package = json.loads(json_str)
            if package['status'] == 'OK':
                dataset = package['dataset']
                mimedata = dataset['zip'].encode('UTF-8')
                msg_bytes = base64.b64decode(mimedata)
                self.fob.upload_binary(msg_bytes, zip_name)

        # import pdb; pdb.set_trace()

        with tempfile.NamedTemporaryFile(suffix='.zip', prefix='tmp-',
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
                        processed = self.process_source(mo, json_data)
                        self.state_count += processed

        dot.end()
        return None

    def process_source(self, mo, json_data):
        bill_state = mo.group(1)
        bill_number = mo.group(3)
        bill_json = json.loads(json_data)

        bill_detail = bill_json['bill']
        session_id = bill_detail['session_id']
        texts = bill_detail['texts']
        # import pdb; pdb.set_trace()

        # If a bill has multiple versions, choose the latest one.
        chosen = self.latest_text(texts)
        extension = self.determine_extension(chosen['mime'])
        bill_year = chosen['date'][:4]

        # Generate the key to be used to refer to this legislation.
        key = self.fob.BillText_key(bill_state, bill_number,
                                    session_id, bill_year)
        bill_id = bill_detail['bill_id']
        title = bill_detail['title']
        summary = bill_detail['description']
        doc_date = chosen['date']
        law_record = Law.objects.filter(key=key).first()
        if law_record is None:
            law_record = Law(key=key, title=title, summary=summary,
                             bill_id=bill_id, doc_date=doc_date,
                             location=self.loc)
            law_record.save()

        text_name = self.fob.BillText_name(key, "txt")

        # If we already have the final text file, honor the --skip parameter
        if self.fob.item_exists(text_name) and self.skip:
            print('File {} already exists, skipping: ', text_name)
            processed = 0
        else:
            processed = self.process_bill(key, extension, bill_detail, chosen)
        return processed

    def process_bill(self, key, extension, bill_detail, chosen):
        bill_name = self.fob.BillText_name(key, extension)
        bill_hash = Hash.find_item_name(bill_name)

        # If the source PDF/HTML exists, and the hash code matches,
        # then it is up-to-date and we can use it directly.
        FOB_source = False
        if (self.fob.item_exists(bill_name)
                and bill_hash is not None
                and bill_hash.hashcode == bill_detail['change_hash']):
            # read the existing PDF/HTML file we have in File/Object store
            FOB_source = True

        processed = 0
        textdata = None
        bindata = None

        if extension == 'html':

            if FOB_source:
                textdata = self.fob.download_text(bill_name)
            else:
                params = {}
                bill_bundle = DataBundle(bill_name)
                source = urlparse(chosen['state_link'])
                print(source.params)
                response = bill_bundle.make_request(source.geturl,
                                                    params)
                result = bill_bundle.load_response(response)
                if result:
                    textdata = bill_bundle.text
                    self.fob.upload_text(textdata, bill_name)

            if textdata:
                self.process_html(key, chosen['date'], bill_detail, textdata)
                processed = 1
            else:
                print('Failure processing HTML source')

        elif extension == 'pdf':
            if FOB_source:
                bindata = self.fob.download_binary(bill_name)
            else:
                params = {}
                bill_bundle = DataBundle(bill_name)
                source = urlparse(chosen['state_link'])
                querylist = source.query.split('&')
                for q in querylist:
                    qfragments = q.split('=')
                    qkey, qvalue = qfragments
                    params[qkey] = qvalue
                scheme = source.scheme
                stem = source.netloc + source.path
                if scheme == '':
                    scheme = 'http'
                baseurl = '{}://{}'.format(scheme, stem)
                response = bill_bundle.make_request(baseurl, params)
                result = bill_bundle.load_response(response)
                import pdb
                pdb.set_trace()
                if result and bill_bundle.content[:4] == b'%PDF':
                    bindata = bill_bundle.content
                    self.fob.upload_binary(bindata, bill_name)
                elif self.api_limit > 0 and self.leg.api_ok:
                    response = self.leg.getBillText(chosen['doc_id'])
                    self.api_limit -= 1
                    if response:
                        json_data = json.loads(response)
                        json_text = json_data['text']
                        json_doc = json_text['doc']

                        mimedata = json_doc.encode('UTF-8')
                        bindata = base64.b64decode(mimedata)
                    

            if bindata:
                self.process_pdf(key, chosen['date'], bill_detail, bindata)
                processed = 1
            else:
                print('Failure processing PDF source')

        if processed:
            self.save_source_hash(bill_hash, bill_name, bill_detail, chosen)
        return processed

    def save_source_hash(self, bill_hash, bill_name, bill_detail, chosen):

        if bill_hash is None:
            hash = Hash()
            hash.item_name = bill_name
            hash.fob_method = settings.FOB_METHOD
            hash.desc = bill_detail['title']
            hash.generated_date = chosen['date']
            hash.hashcode = bill_detail['change_hash']
            hash.size = chosen['text_size']
            hash.save()

        else:
            bill_hash.generated_date = chosen['date']
            bill_hash.hashcode = bill_detail['change_hash']
            bill_hash.size = chosen['text_size']
            bill_hash.save()

        return None

    def fetch_file_from_state(self, bill_name, chosen):
        params = {}
        bill_bundle = DataBundle(bill_name)
        response = bill_bundle.make_request(chosen['state_link'], params)
        result = bill_bundle.load_response(response)
        return result

    def process_html(self, key, docdate, bill_detail, billtext):
        bill_name = self.fob.BillText_name(key, 'html')
        text_name = self.fob.BillText_name(key, 'txt')

        text_line = Oneline()
        title, summary = bill_detail['title'], bill_detail['description']
        text_line.add_text(HeadForm.format(bill_name, docdate, title, summary))
        self.parse_html(billtext, text_line)
        text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(text_name)
        print('Writing: ', text_name)
        return self

    def process_pdf(self, key, docdate, bill_detail, msg_bytes):

        input_str = ""
        # import pdb; pdb.set_trace()
        temp_name = self.rand_key + ".pdf"
        temp_path = os.path.join(settings.SOURCE_ROOT, temp_name)
        with open(temp_path, "wb") as outfile:
            outfile.write(msg_bytes)

        with tempfile.NamedTemporaryFile(suffix='.txt', prefix='tmp-',
                                         delete=True) as temp_out:
            PDFtoTEXT(temp_path, temp_out.name)
            temp_out.seek(0)
            input_str = temp_out.read().decode('UTF-8')

        bill_name = self.fob.BillText_name(key, 'pdf')
        title, summary = bill_detail['title'], bill_detail['description']
        header = HeadForm.format(bill_name, docdate, title, summary)

        text_name = self.fob.BillText_name(key, 'txt')
        text_line = Oneline()
        text_line.add_text(header)
        if input_str:
            self.parse_intermediate(input_str, text_line)
            text_line.oneline = self.remove_section_numbers(text_line.oneline)
        text_line.write_name(text_name)
        print('Writing: ', text_name)
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
        if self.api_limit > 0 and self.leg.api_ok:
            try:
                response = self.leg.getBillText(docID)
            except Exception as e:
                self.leg.api_ok = False
                print('Error: {}'.format(e))
                raise LegiscanError('Unable to fetch bill: '+key+" "+docID)

        if response:
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
        LastDate = settings.LONG_AGO

        LastDocid = 0
        LastEntry = None
        for entry in texts:
            this_date = self.date_type(entry['date'])
            this_docid = entry['doc_id']
            if (this_date > LastDate or
                    (this_date == LastDate and this_docid > LastDocid)):
                LastDate = this_date
                LastDocid = this_docid
                LastEntry = entry

        return LastEntry

    def date_type(self, date_string):
        """ Convert "YYYY-MM-DD" string to datetime.date format """
        date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
        return date_value
