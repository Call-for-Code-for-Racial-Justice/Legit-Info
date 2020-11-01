#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
From legislative session datasets, extract PDF/HTML and extract text.

This is phase 2 of weekly cron job.  See CRON.md for details.
Invoke with ./stage1 extract_files  or ./cron1 extract_files
Specify --help for details on parameters available.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import base64
import datetime as DT
import json
import logging
from urllib.parse import urlparse
import nltk
from bs4 import BeautifulSoup
import zipfile
from titlecase import titlecase
import tempfile
import re

# Django and other third-party imports
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# Application imports
from cfc_app.DataBundle import DataBundle
from cfc_app.Oneline import Oneline
from cfc_app.LegiscanAPI import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.models import Law, Location, Hash
from cfc_app.PDFtoTEXT import PDFtoTEXT
from cfc_app.ShowProgress import ShowProgress
from cfc_app.FOB_Storage import FOB_Storage

# Debug with:   import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

PARSER = "lxml"
TITLE_LIMIT = 200
SUMMARY_LIMIT = 1000

# Put the original file name, doc date, title and summary ahead of text

FileForm = "_FILE_ {}"
HashForm = " _HASHCODE_ "
DateForm = " _DOCDATE_ {}"
BillForm = " _BILLID_ {}"
CiteForm = " _CITE_ {}"
TitleForm = " _TITLE_ {}"
SumForm = " _SUMMARY_ {}"
TextForm = " _TEXT_ "

billRegex = re.compile(r"^([A-Z]{2})/\d\d\d\d-(\d\d\d\d).*/bill/(\w*).json$")

nameForm = "{}.{}"


class ExtractError(CommandError):
    pass


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
        self.dot = ShowProgress()
        self.api_limit = 0
        self.state = None
        self.billno = None
        self.session_id = None
        self.limit = 10
        self.skip = False
        self.state_count = 0
        self.verbosity = 1  # System default is dots and error messages only
        nltk.download('punkt')
        self.nltk_loaded = True
        self.starting_msg = ""
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API, if needed")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--session_id", help="Process this session only")
        parser.add_argument("--bill", help="Process this bill number only")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Number of bills to extract per state")
        parser.add_argument("--skip", action="store_true",
                            help="Skip files already in File/Object storage")

        return None

    def handle(self, *args, **options):

        try:
            self.parse_options(options)
        except Exception as e:
            err_msg = '116: Parse Error input options. {}'.format(e)
            logger.error(err_msg, exc_info=True)
            raise ExtractError(err_msg)

        # import pdb; pdb.set_trace()
        logger.info(self.starting_msg)

        # Use the Django "Location" database to get list of locations
        # listed with valid (non-zero) Legiscan_id.  For example,
        # Legiscan_id=3 for Arizona, and Legiscan_id=35 for Ohio.

        locations = Location.objects.filter(legiscan_id__gt=0)

        for loc in locations:
            if self.verbosity:
                self.dot.show()
            self.loc = loc
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            # If we are only processing one state, and this is
            # not it, continue to the next state.
            if self.state and (state != self.state):
                continue

            logger.info('155:Processing: {} ({})'.format(loc.desc, state))
            self.state_count = 0
            found_list = self.fob.Dataset_items(state)

            sessions = []
            found_list.sort(reverse=True)
            for json_name in found_list:
                if self.verbosity:
                    self.dot.show()
                mo = self.fob.Dataset_search(json_name)
                if mo:
                    state = mo.group(1)
                    session_id = mo.group(2)
                    logger.debug('168: Session_id: '+session_id)
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
                if self.verbosity:
                    self.dot.show()
                if self.limit > 0 and self.state_count >= self.limit:
                    break
                session_id, json_name = session_detail
                logger.debug("173:Session_id={} JSON={}".format(session_id,
                                                                json_name))
                try:
                    self.process_json(state, session_id, json_name)
                except Exception as e:
                    err_msg = '178: Process Error. {}'.format(e)
                    logger.error(err_msg, exc_info=True)
                    raise ExtractError(err_msg)

        return None

    def parse_options(self, options):
        starting = '====STARTING: extract_files'
        if options['api']:
            self.api_limit = 10
            starting += ' --api'

        starting_state = ''
        if options['state']:
            self.state = options['state']
            starting_state += ' --state '+self.state

        self.limit = options['limit']
        starting = "{} --limit {}".format(starting, self.limit)

        if options['skip']:
            self.skip = True
            starting += ' --skip'

        self.verbosity = options['verbosity']   # Default is 1
        starting = "{} --verbosity {}".format(starting, self.verbosity)

        if options['session_id']:
            self.session_id = options['session_id']
            starting += ' --session_id '+self.session_id
            self.state = None
        else:
            starting += starting_state

        if options["bill"]:
            self.billno = options["bill"]
            starting += self.billno

        self.starting_msg = starting

        return None

    def process_json(self, state, session_id, json_name):
        """ Process CC-Dataset-NNNN.json file """

        logger.debug('196:Checking JSON: '+json_name)
        json_str = self.fob.download_text(json_name)

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
                        bill_number = mo.group(3)
                        if self.billno and bill_number != self.billno:
                            continue

                        if self.verbosity:
                            self.dot.show()

                        logger.debug('229:PATH name: '+path)
                        json_data = zf.read(path).decode('UTF-8',
                                                         errors='ignore')

                        logger.debug('232:JD: '+json_data[:75])
                        processed = self.process_source(mo, json_data)
                        self.state_count += processed

        self.dot.end()
        return None

    def process_source(self, mo, json_data):
        """ Process the PDF/HTML source file """
        processed = 0
        bill_state = mo.group(1)
        bill_number = mo.group(3)

        bill_json = json.loads(json_data)
        logger.debug('245:state={} bill_number={}'.format(bill_state,
                                                          bill_number))

        bill_detail = bill_json['bill']
        session_id = bill_detail['session_id']
        texts = bill_detail['texts']

        # If a bill has multiple versions, choose the latest one.
        if texts:
            earliest_year, chosen = self.latest_text(texts)
            extension = self.determine_extension(chosen['mime'])
        else:
            warn_msg = "293:No texts found for {}-{}-{}"
            logger.warning(warn_msg.format(
                bill_state, bill_number, session_id))
            return processed

        # Generate the key to be used to refer to this legislation.
        key = self.fob.BillText_key(bill_state, bill_number,
                                    session_id, earliest_year)
        bill_detail['bill_number'] = bill_number
        bill_detail['key'] = key
        bill_id = bill_detail['bill_id']
        title = titlecase(bill_detail['title'])
        bill_detail['title'] = title
        summary = bill_detail['description']
        doc_date = chosen['date']
        bill_detail['doc_date'] = doc_date
        bill_detail['doc_size'] = chosen['text_size']
        law_record = Law.objects.filter(key=key).first()
        if law_record is None:
            logger.debug('267:Creating LAW record '+key)
            law_record = Law(key=key, title=title, summary=summary,
                             bill_id=bill_id, doc_date=doc_date,
                             location=self.loc)
            law_record.save()
        else:
            logger.debug("275:LAW record already exists "+key)

        text_name = self.fob.BillText_name(key, "txt")

        # If we already have the final text file, honor the --skip parameter

        skipping = False
        processed = 0
        if self.fob.item_exists(text_name):
            if self.skip:
                skip_msg = 'File {} already exists, skipping'.format(text_name)
                logger.debug("282:"+skip_msg)
                if self.verbosity > 2:
                    print(skip_msg)
                elif self.verbosity:
                    self.dot.show(char='>')
                processed = 0
                skipping = True
            else:
                textdata = self.fob.download_text(text_name)
                headers = Oneline.parse_header(textdata)
                if ('CITE' in headers
                        and headers['CITE'][:8] != 'Legiscan'
                        and headers['CITE'][-7:] != 'general'):
                    bill_detail['cite_url'] = headers['CITE']
                    logger.debug('297:OLD CITE_URL={}'.format(headers['CITE']))
                elif ('CITE' in headers
                        and headers['CITE'][:8] == 'Legiscan'):
                    # No URL found, remove it so it is re-built next
                    cite = "http://legiscan.com/{}/{}/{}".format(
                        bill_state, bill_number, bill_detail['doc_date'][:4])
                    bill_detail['cite_url'] = cite
                    logger.debug('297:NEW CITE_URL={}'.format(cite))

        if not skipping:
            processed = self.process_bill(key, extension, bill_detail, chosen)
        return processed

    def process_bill(self, key, extension, bill_detail, chosen):
        """ process individual PDF/HTML bill """

        bill_name = self.fob.BillText_name(key, extension)
        bill_hash = Hash.find_item_name(bill_name)
        logger.debug('311:bill_name={} bill_hash={}'.format(bill_name,
                                                            bill_hash))

        # If the source PDF/HTML exists, and the hash code matches,
        # then it is up-to-date and we can use it directly.
        FOB_source = False
        if (self.fob.item_exists(bill_name)
                and bill_hash is not None
                and bill_hash.hashcode == bill_detail['change_hash']):
            # read the existing PDF/HTML file we have in File/Object store
            FOB_source = True

        processed = 0
        bindata = None
        source_file = bill_name

        if FOB_source:
            logger.debug('328:Reading existing: '+bill_name)
            bindata = self.fob.download_binary(bill_name)
            source_file = "{} ({})".format(bill_name, settings.FOB_METHOD)

        else:
            params = {}
            bill_bundle = DataBundle(bill_name)
            source = urlparse(chosen['state_link'])
            source_file = chosen['state_link']
            logger.debug('337:state_link={}'.format(chosen['state_link']))
            if 'cite_url' not in bill_detail:
                bill_detail['cite_url'] = source_file

            if source.query:
                querylist = source.query.split('&')
                for q in querylist:
                    qfragments = q.split('=')
                    if len(qfragments) == 2:
                        qkey, qvalue = qfragments
                        params[qkey] = qvalue
            scheme = source.scheme
            stem = source.netloc + source.path
            if scheme == '':
                scheme = 'http'
            baseurl = '{}://{}'.format(scheme, stem)
            response = bill_bundle.make_request(baseurl, params)
            result = bill_bundle.load_response(response)
            # import pdb; pdb.set_trace()
            if result:
                bindata = bill_bundle.content
                if extension == "pdf" and bindata[:4] != b'%PDF':
                    logger.error("352:Invalid PDF format found: "+bill_name)
                    bindata = None

            if bindata:
                self.fob.upload_binary(bindata, bill_name)
                saving_msg = "Saving file: {}".format(bill_name)
                logger.debug("358:"+saving_msg)
                if self.verbosity > 2:
                    print(saving_msg)

            elif self.api_limit > 0 and self.leg.api_ok:
                warn_msg = "363:Invoking Legiscan API: {} doc_id={}"
                logger.warning(warn_msg.format(bill_name, chosen['doc_id']))
                response = self.leg.getBillText(chosen['doc_id'])
                source_file = "getBillText doc_id="+str(chosen['doc_id'])
                if 'cite_url' not in bill_detail:
                    cite = "http://legiscan.com/{}/{}/{}".format(
                        key[:2], bill_detail['bill_number'],
                        bill_detail['doc_date'][:4])
                    bill_detail['cite_url'] = cite
                self.api_limit -= 1
                if response:
                    json_data = json.loads(response)
                    json_text = json_data['text']
                    json_doc = json_text['doc']
                    mimedata = json_doc.encode('UTF-8')
                    bindata = base64.b64decode(mimedata)

        # For HTML, convert to text.  Othewise leave binary for PDF.
        if bindata and extension == 'html':
            textdata = bindata.decode('UTF-8', errors='ignore')
            self.process_html(key, chosen['date'], bill_detail, textdata)
            processed = 1
        elif bindata and extension == 'pdf':
            self.process_pdf(key, chosen['date'], bill_detail, bindata)
            processed = 1

        # If successful, save the hash code to the cfc_app_hash table
        if processed:
            self.save_source_hash(bill_hash, bill_name, bill_detail, chosen)
            self.dot.show()
        else:
            logger.error('391:Failure processing source: ' + source_file)
        return processed

    def save_source_hash(self, bill_hash, bill_name, bill_detail, chosen):

        if bill_hash is None:
            hash = Hash()
            hash.item_name = bill_name
            hash.fob_method = settings.FOB_METHOD
            hash.desc = bill_detail['title']
            hash.generated_date = bill_detail['doc_date']
            hash.hashcode = bill_detail['change_hash']
            hash.size = bill_detail['doc_size']
            logger.debug('417:INSERT cfc_app_law:{}'.format(bill_name))
            hash.save()

        else:
            bill_hash.generated_date = bill_detail['doc_date']
            bill_hash.hashcode = bill_detail['change_hash']
            bill_hash.size = bill_detail['doc_size']
            logger.debug('424:UPDATE cfc_app_law:{}'.format(bill_name))
            bill_hash.save()

        return None

    def process_html(self, key, docdate, bill_detail, billtext):
        bill_name = self.fob.BillText_name(key, 'html')
        text_name = self.fob.BillText_name(key, 'txt')

        text_line = Oneline(nltk_loaded=True)

        self.add_header(text_line, bill_name, bill_detail)
        self.parse_html(billtext, text_line)
        self.write_file(text_line, text_name)
        return self

    def write_file(self, text_line, text_name):
        text_line.split_sentences()
        logger.info('428:Writing: ' + text_name)
        self.fob.upload_text(text_line.oneline, text_name)
        return

    def process_pdf(self, key, docdate, bill_detail, msg_bytes):
        """ Parse PDF file to extract text """

        logger.debug("435:key={}".format(key))
        input_str = ""

        bill_name = self.fob.BillText_name(key, 'pdf')
        miner = PDFtoTEXT(bill_name, msg_bytes)
        input_str = miner.convert_to_text()

        if input_str:
            text_name = self.fob.BillText_name(key, 'txt')
            text_line = Oneline(nltk_loaded=True)
            self.add_header(text_line, bill_name, bill_detail)
            self.parse_intermediate(input_str, text_line)
            self.write_file(text_line, text_name)

        return self

    def add_header(self, text_line, bill_name, bill_detail):
        """ Put header information in the text file itself """

        text_line.header_file_name(bill_name)
        text_line.header_bill_id(bill_detail['bill_id'])
        text_line.header_doc_date(bill_detail['doc_date'])
        text_line.header_hash_code(bill_detail['change_hash'])
        if 'cite_url' in bill_detail:
            text_line.header_cite_url(bill_detail['cite_url'])
        text_line.header_title(bill_detail['title'])
        text_line.header_summary(bill_detail['description'])
        text_line.header_end()
        return None

    def form_sentence(self, line, charlimit):

        # Remove trailing spaces, and add period at end of sentence.
        newline = line.strip()
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
                fetch_msg = "Unable to fetch bill: key={} DocID={} Msg:{}"
                logger.error(fetch_msg.format(key, docID, e), exc_info=True)
                raise LegiscanError('Unable to fetch bill')

        if response:
            mime_type = response['mime_type']
            extension = self.determine_extension(mime_type)

            mimedata = response['doc'].encode('UTF-8')
            msg_bytes = base64.b64decode(mimedata)

            billname = '{}.{}'.format(key, extension)
            logger.debug('Getting from Legiscan: '+billname)

        if extension == 'html':
            billtext = msg_bytes.decode('UTF-8', errors='ignore')
            self.fob.upload_text(billtext, billname)
        elif extension == 'pdf':
            self.fob.upload_binary(msg_bytes, billname)

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
                pg = re.sub(r"^([0-9]{1,2})[.] ", r"(\1) ", pg)
                pg = re.sub(r"^([A-Za-z])[.] ", r"(\1) ", pg)
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

    def latest_text(self, texts):
        LastDate = settings.LONG_AGO

        LastDocid = 0
        LastEntry = None
        earliest_year = 2999
        for entry in texts:
            this_date = self.date_type(entry['date'])
            this_docid = entry['doc_id']
            if this_date.year < earliest_year:
                earliest_year = this_date.year
            if (this_date > LastDate or
                    (this_date == LastDate and this_docid > LastDocid)):
                LastDate = this_date
                LastDocid = this_docid
                LastEntry = entry

        return earliest_year, LastEntry

    def date_type(self, date_string):
        """ Convert "YYYY-MM-DD" string to datetime.date format """
        date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
        return date_value
