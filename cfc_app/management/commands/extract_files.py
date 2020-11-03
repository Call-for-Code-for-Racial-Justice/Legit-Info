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
import re
import tempfile
from urllib.parse import urlparse
import zipfile

# Django and other third-party imports
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import nltk
from titlecase import titlecase


# Application imports
from cfc_app.data_bundle import DataBundle
from cfc_app.fob_storage import FOB_Storage
from cfc_app.legiscan_api import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.log_time import LogTime
from cfc_app.models import Law, Location, Hash
from cfc_app.one_line import Oneline
from cfc_app.pdf_to_text import PDFtoText
from cfc_app.show_progress import ShowProgress

# Debug with:   import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

PARSER = "lxml"
TITLE_LIMIT = 200
SUMMARY_LIMIT = 1000

# Put the original file name, doc date, title and summary ahead of text

billRegex = re.compile(r"^([A-Z]{2})/\d\d\d\d-(\d\d\d\d).*/bill/(\w*).json$")

###############################################
#  Support functions
###############################################


def add_header(text_line, bill_name, bill_detail):
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


def date_type(date_string):
    """ Convert "YYYY-MM-DD" string to datetime.date format """
    date_value = DT.datetime.strptime(date_string, "%Y-%m-%d").date()
    return date_value


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


def parse_url(bill_detail):
    """ parse state_link into baseurl and params """

    state_link = bill_detail['chosen']['state_link']
    source = urlparse(state_link)
    logger.debug(f"96:state_link={state_link}")
    if 'cite_url' not in bill_detail:
        bill_detail['cite_url'] = state_link

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


def save_source_hash(bill_hash, bill_name, bill_detail):
    """ Save hashcode to cfc_app_hash table """

    if bill_hash is None:
        bill_hash = Hash()
        bill_hash.item_name = bill_name
        bill_hash.fob_method = settings.FOB_METHOD
        bill_hash.desc = bill_detail['title']
        bill_hash.generated_date = bill_detail['doc_date']
        bill_hash.hashcode = bill_detail['change_hash']
        bill_hash.size = bill_detail['doc_size']
        logger.debug(f"449:INSERT cfc_app_law: {bill_name}")
        bill_hash.save()

    else:
        bill_hash.generated_date = bill_detail['doc_date']
        bill_hash.hashcode = bill_detail['change_hash']
        bill_hash.size = bill_detail['doc_size']
        logger.debug(f"456:UPDATE cfc_app_law: {bill_name}")
        bill_hash.save()

    return None


def shrink_line(line, charlimit):
    """ if chopping a line from the front, find next full word """

    newline = re.sub(r'^\W*\w*\W*', '', line[-charlimit:])
    newline = re.sub(r'^and ', '', newline)
    newline = newline[0].upper() + newline[1:]
    return newline


class ExtractTextError(CommandError):
    """ Customized Error class """
    pass


class Command(BaseCommand):
    """ Customized Django command for CRON job """

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
        self.loc = None
        self.dot = ShowProgress()
        self.api_limit = 0
        self.state = None
        self.session_id = None
        self.limit = 10
        self.skip = False
        self.state_count = 0
        self.verbosity = 1  # System default is dots and error messages only
        nltk.download('punkt')
        self.nltk_loaded = True
        self.after = None
        return None

    def add_arguments(self, parser):
        """ Parse arguments """

        parser.add_argument("--api", action="store_true",
                            help="Invoke Legiscan.com API, if needed")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--session_id", help="Process this session only")
        parser.add_argument("--after", help="Start after this item name")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="Number of bills to extract per state")
        parser.add_argument("--skip", action="store_true",
                            help="Skip files already in File/Object storage")

        return None

    def handle(self, *args, **options):
        """ Main handler for customized DJANGO command """

        timing = LogTime("extract_files")
        timing.start_time(options['verbosity'])

        try:
            self.parse_options(options)
        except Exception as exc:
            err_msg = f"116: Parse Error input options: {exc}"
            logger.error(err_msg, exc_info=True)
            raise ExtractTextError from exc

        # import pdb; pdb.set_trace()
        logger.info(self.starting_msg)

        # Use the Django "Location" database to get list of locations
        # listed with valid (non-zero) Legiscan_id.  For example,
        # Legiscan_id=3 for Arizona, and Legiscan_id=35 for Ohio.

        locations = Location.objects.filter(legiscan_id__gt=0)

        for loc in locations:
            self.loc = loc

            if self.verbosity:
                self.dot.show()
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            # If we are only processing one state, and this is
            # not it, continue to the next state.
            if (self.state is None) or (state == self.state):
                logger.info(f"136:Processing: {loc.desc} ({state})")
                self.process_location(state)

        timing.end_time(options['verbosity'])
        return None

    def process_location(self, state):
        """ Extract files for this state """

        self.state_count = 0
        found_list = self.fob.Dataset_items(state)

        sessions = []
        found_list.sort(reverse=True)
        for json_name in found_list:
            if self.verbosity:
                self.dot.show()
            mop = self.fob.Dataset_search(json_name)
            if mop:
                state = mop.group(1)
                session_id = mop.group(2)
                logger.debug(f"149: Session_id: {session_id}")
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
            logger.debug(f"168:Session_id={session_id} JSON={json_name}")
            try:
                self.process_json(json_name)
            except Exception as exc:
                err_msg = f"172: Process Error. {exc}"
                logger.error(err_msg, exc_info=True)
                raise ExtractTextError(err_msg) from exc

        return None

    def parse_options(self, options):
        """ Validate processing options """

        logger.debug(f"182:Options {options}")

        if options['api']:
            self.api_limit = 10

        if options['state']:
            self.state = options['state']

        self.limit = options['limit']

        if options['skip']:
            self.skip = True

        self.verbosity = options['verbosity']   # Default is 1

        if options['session_id']:
            self.session_id = options['session_id']
            self.state = None

        if options["after"]:
            self.after = options["after"]

        return None

    def process_json(self, json_name):
        """ Process CC-Dataset-NNNN.json file """

        logger.debug(f"209:Checking JSON: {json_name}")
        json_str = self.fob.download_text(json_name)

        # If the ZIP file already exists, use it, otherwise create it.
        zip_name = json_name.replace('.json', '.zip')
        msg_bytes = b""
        if self.fob.item_exists(zip_name):
            msg_bytes = self.fob.download_binary(zip_name)
        else:
            package = json.loads(json_str)
            if package['status'] == 'OK':
                dataset = package['dataset']
                mimedata = dataset['zip'].encode('UTF-8')
                msg_bytes = base64.b64decode(mimedata)
                self.fob.upload_binary(msg_bytes, zip_name)

        if msg_bytes:
            self.process_zip(msg_bytes)

        self.dot.end()
        return None

    def process_zip(self, msg_bytes):
        """ Process ZIP package in temporary file """

        with tempfile.NamedTemporaryFile(suffix='.zip', prefix='tmp-',
                                         delete=True) as temp_zip:
            temp_zip.write(msg_bytes)
            temp_zip.seek(0)

            with zipfile.ZipFile(temp_zip.name, 'r') as zipf:
                namelist = zipf.namelist()

                for path in namelist:

                    if self.limit > 0 and self.state_count >= self.limit:
                        break
                    mop = billRegex.search(path)
                    if mop:
                        if self.verbosity:
                            self.dot.show()

                        logger.debug(f"315:PATH name: {path}")
                        json_data = zipf.read(path).decode('UTF-8',
                                                           errors='ignore')

                        logger.debug(f"247:JD: {json_data[:75]}")
                        processed = self.process_source(mop, json_data)
                        self.state_count += processed
        return None

    def process_source(self, mop, json_data):
        """ Process the PDF/HTML source file """

        processed = 0
        bill_json = json.loads(json_data)
        bill_detail = bill_json['bill']

        bill_detail['state'] = mop.group(1)
        bill_detail['bill_number'] = mop.group(3)
        logger.debug(f"262:state={bill_detail['state']} "
                     f"bill_number={bill_detail['bill_number']}")
        texts = bill_detail['texts']

        # If a bill has multiple versions, choose the latest one.
        if texts:
            earliest_year, chosen = self.latest_text(texts)
            bill_detail['chosen'] = chosen
            bill_detail['extension'] = self.determine_extension(chosen['mime'])
            bill_detail['doc_date'] = chosen['date']
            bill_detail['doc_size'] = chosen['text_size']

            # Generate the key to be used to refer to this legislation.
            key = self.fob.BillText_key(bill_detail['state'],
                                        bill_detail['bill_number'],
                                        bill_detail['session_id'],
                                        earliest_year)
            bill_detail['key'] = key

            if (self.after is None) or (self.after < key):

                self.process_detail(bill_detail, key)
                # If we already have extracted the text file,
                # honor the --skip parameter
                text_name = self.fob.BillText_name(key, "txt")
                processed = self.skip_if_exists(text_name, bill_detail)

        else:
            logger.warning(f"273:No texts found for {bill_detail['state']}-"
                           f"{bill_detail['bill_number']}-"
                           f"{bill_detail['session_id']}")

        return processed

    def process_detail(self, bill_detail, key):
        """ Process bill detail """

        bill_id = bill_detail['bill_id']
        title = titlecase(bill_detail['title'])
        bill_detail['title'] = title
        summary = bill_detail['description']

        law_record = Law.objects.filter(key=key).first()
        if law_record is None:
            logger.debug(f"296:Creating LAW record: {key}")
            law_record = Law(key=key, title=title, summary=summary,
                             bill_id=bill_id, location=self.loc,
                             doc_date=bill_detail['description'])
            law_record.save()
        else:
            logger.debug("302:LAW record already exists: {key}")

        return None

    def skip_if_exists(self, text_name, bill_detail):
        """ check if file exists """

        skipping = False
        processed = 0
        if self.fob.item_exists(text_name):
            if self.skip:
                skip_msg = f"File {text_name} already exists, skipping"
                logger.debug("381:SKIP {skip_msg}")
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
                    logger.debug(f"327:OLD CITE_URL={headers['CITE']}")
                elif (('CITE' in headers)
                      and (headers['CITE'][:8] == 'Legiscan')):
                    # No URL found, remove it so it is re-built next
                    cite = "http://legiscan.com/{}/{}/{}".format(
                        bill_detail['state'], bill_detail['bill_number'],
                        bill_detail['doc_date'][:4])
                    bill_detail['cite_url'] = cite
                    logger.debug(f"334:NEW CITE_URL={cite}")

        if not skipping:
            processed = self.process_bill(bill_detail)

        return processed

    def process_bill(self, bill_detail):
        """ process individual PDF/HTML bill """

        key = bill_detail['key']
        bill_name = self.fob.BillText_name(key, bill_detail['extension'])
        bill_hash = Hash.find_item_name(bill_name)
        logger.debug(f"345:bill_name={bill_name} bill_hash={bill_hash}")

        # If the source PDF/HTML exists, and the hash code matches,
        # then it is up-to-date and we can use it directly.
        fob_source = False
        if (self.fob.item_exists(bill_name)
                and bill_hash is not None
                and bill_hash.hashcode == bill_detail['change_hash']):
            # read the existing PDF/HTML file we have in File/Object store
            fob_source = True

        processed = 0
        bindata = None
        source_file = bill_name

        if fob_source:
            logger.debug(f"361:Reading existing: {bill_name}")
            bindata = self.fob.download_binary(bill_name)
            source_file = "{} ({})".format(bill_name, settings.FOB_METHOD)
        else:
            bindata = self.fetch_state_link(bill_detail)

        # For HTML, convert to text.  Othewise leave binary for PDF.
        extension = bill_detail['extension']
        if bindata and extension == 'html':
            textdata = bindata.decode('UTF-8', errors='ignore')
            self.process_html(key, bill_detail, textdata)
            processed = 1
        elif bindata and extension == 'pdf':
            self.process_pdf(key, bill_detail, bindata)
            processed = 1

        # If successful, save the hash code to the cfc_app_hash table
        if processed:
            self.save_source_hash(bill_hash, bill_name, bill_detail)
            self.dot.show()
        else:
            logger.error(f"435:Failure processing source: {source_file}")
        return processed

    def fetch_state_link(self, bill_detail):
        """ Fetch PDF/HTML from State Link or Legiscan.com API """

        bill_name = bill_detail['bill_name']
        bill_bundle = DataBundle(bill_name)

        baseurl, params = parse_url(bill_detail)

        response = bill_bundle.make_request(baseurl, params)
        result = bill_bundle.load_response(response)
        # import pdb; pdb.set_trace()
        if result:
            bindata = bill_bundle.content
            if ((bill_detail['extension'] == "pdf")
                    and (bindata[:4] != b'%PDF')):
                logger.error(f"392:Invalid PDF format found: {bill_name}")
                bindata = None

        if bindata:
            self.fob.upload_binary(bindata, bill_name)
            saving_msg = f"Saving file: {bill_name}"
            logger.debug(f"398: {saving_msg}")
            if self.verbosity > 2:
                print(saving_msg)

        elif self.api_limit > 0 and self.leg.api_ok:
            bindata = self.fetch_legiscan_api(bill_detail)

        return bindata

    def fetch_legiscan_api(self, bill_detail):
        """ Fetch from Legiscan API using getBillText command """

        bindata = b""
        bill_name = bill_detail['bill_name']
        state = bill_detail['state']
        doc_id = bill_detail['chosen']['doc_id']
        doc_year = bill_detail['doc_date'][:4]
        logger.warning(f"403:Invoking Legiscan API: {bill_name} "
                       f"doc_id={doc_id}")
        response = self.leg.getBillText(doc_id)
        if 'cite_url' not in bill_detail:
            cite = (f"http://legiscan.com/{state}/"
                    f"{bill_detail['bill_number']}/{doc_year}")
            bill_detail['cite_url'] = cite
        self.api_limit -= 1
        if response:
            json_data = json.loads(response)
            json_text = json_data['text']
            json_doc = json_text['doc']
            mimedata = json_doc.encode('UTF-8')
            bindata = base64.b64decode(mimedata)

        return bindata

    def process_html(self, key, bill_detail, billtext):
        """ Process HTML source file of legislation """

        bill_name = self.fob.BillText_name(key, 'html')
        text_name = self.fob.BillText_name(key, 'txt')

        text_line = Oneline(nltk_loaded=True)

        self.add_header(text_line, bill_name, bill_detail)
        self.parse_html(billtext, text_line)
        self.write_file(text_line, text_name)
        return self

    def write_file(self, text_line, text_name):
        """ Write text file as series of full sentences  """

        text_line.split_sentences()
        logger.info(f"478:Writing: {text_name}")
        self.fob.upload_text(text_line.oneline, text_name)
        return

    def process_pdf(self, key, bill_detail, msg_bytes):
        """ Parse PDF file to extract text """

        logger.debug("485:key={key}")
        input_str = ""

        bill_name = self.fob.BillText_name(key, 'pdf')
        miner = PDFtoText(bill_name, msg_bytes)
        input_str = miner.convert_to_text()

        if input_str:
            text_name = self.fob.BillText_name(key, 'txt')
            text_line = Oneline(nltk_loaded=True)
            self.add_header(text_line, bill_name, bill_detail)
            self.parse_intermediate(input_str, text_line)
            self.write_file(text_line, text_name)

        return self

    def form_sentence(self, line, charlimit):
        """ Reduce title/summary to fit within character limits """

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
        """ If not available from the state, fetch from Legiscan.com API """

        extension, msg_bytes = '', b''
        doc_id = bill['doc_id']
        response = ''
        if self.api_limit > 0 and self.leg.api_ok:
            try:
                response = self.leg.get_bill_text(doc_id)
            except Exception as exc:
                self.leg.api_ok = False
                ftext = 'Unable to fetch bill'
                logger.error(f"{ftext}: key={key} DocID={doc_id} Msg:{exc}",
                             exc_info=True)
                raise LegiscanError(ftext) from exc

        if response:
            mime_type = response['mime_type']
            extension = self.determine_extension(mime_type)

            mimedata = response['doc'].encode('UTF-8')
            msg_bytes = base64.b64decode(mimedata)

            billname = f"{key}.{extension}"
            logger.debug(f"Getting from Legiscan: {billname}")

        if extension == 'html':
            billtext = msg_bytes.decode('UTF-8', errors='ignore')
            self.fob.upload_text(billtext, billname)
        elif extension == 'pdf':
            self.fob.upload_binary(msg_bytes, billname)

        return extension, msg_bytes

    def parse_html(self, in_line, out_line):
        """ Use BeautifulSoup libraries to parse HTML """

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
            prg = paragraph.string
            if prg:
                prg = re.sub(r"^([0-9]{1,2})[.] ", r"(\1) ", prg)
                prg = re.sub(r"^([A-Za-z])[.] ", r"(\1) ", prg)
                out_line.add_text(prg)

        return self

    def parse_intermediate(self, input_string, output_line):
        """ Parse the intermediate file from pdf_to_text conversion """

        lines = input_string.splitlines()
        for line in lines:
            newline = line.replace('B I L L', 'BILL')
            newline = newline.strip()
            # Remove lines that only contain blanks or line numbers only
            if newline != '' and not newline.isdigit():
                output_line.add_text(newline)
        return self

    def latest_text(self, texts):
        """ If legislation has two or more documents, pick the latest one """

        last_date = settings.LONG_AGO

        last_docid = 0
        last_entry = None
        earliest_year = 2999
        for entry in texts:
            this_date = self.date_type(entry['date'])
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
