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
import zipfile

# Django and other third-party imports
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import nltk
from titlecase import titlecase


# Application imports
from cfc_app.bill_detail import BillDetail
from cfc_app.data_bundle import DataBundle
from cfc_app.fob_storage import FobStorage
from cfc_app.fob_helper import FobHelper
from cfc_app.legiscan_api import LegiscanAPI, LEGISCAN_ID, LegiscanError
from cfc_app.log_time import LogTime
from cfc_app.models import Law, Location, Hash, save_source_hash
from cfc_app.Oneline import Oneline, Oneline_add_header
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
        self.fob = FobStorage(settings.FOB_METHOD)
        self.fobhelp = FobHelper(self.fob)
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
        self.now = DT.datetime.today().date()
        self.fromyear = self.now.year - 2  # Back three years 2018, 2019, 2020
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
                logger.info(f"194:Processing: {loc.longname} ({state})")
                self.process_location(state)

        timing.end_time(options['verbosity'])
        return None

    def process_location(self, state):
        """ Extract files for this state """

        self.state_count = 0
        found_list = self.fobhelp.dataset_items(state)

        sessions = []
        found_list.sort(reverse=True)
        for json_name in found_list:
            if self.verbosity:
                self.dot.show()
            mop = self.fobhelp.dataset_search(json_name)
            if mop:
                state = mop.group(1)
                session_id = mop.group(2)
                logger.debug(f"215: Session_id: {session_id}")
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
            logger.debug(f"234:Session_id={session_id} JSON={json_name}")
            try:
                self.process_json(json_name)
            except Exception as exc:
                err_msg = f"238: Process Error. {exc}"
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

        source_hash = Hash.find_item_name(json_name)

        zip_name = json_name.replace('.json', '.zip')
        target_hash = Hash.find_item_name(zip_name)
        if target_hash is None:
            target_hash = Hash(item_name=zip_name,
                               fob_method=settings.FOB_METHOD,
                               generated_date=source_hash.generated_date,
                               hashcode=source_hash.hashcode,
                               objsize=source_hash.objsize,
                               legdesc=source_hash.legdesc)
            logger.debug(f"Hashcode for {zip_name} saved.")
            target_hash.save()

        # If the ZIP file already exists, use it, otherwise create it.

        msg_bytes = b""
        if (self.fob.item_exists(zip_name)
                and source_hash.generated_date <= target_hash.generated_date):
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
                        logger.debug(f"315:PATH name: {path}")
                        json_data = zipf.read(path).decode('UTF-8',
                                                           errors='ignore')
                        logger.debug(f"320:JD: {json_data[:75]}")
                        processed = self.process_source(json_data)
                        self.state_count += processed

                        # Verbosity: -v 0 no dots, -v 1 normal dots
                        #            -v 2 dots + path every 100 entries
                        #            -v 3 print every path that matches
                        if self.verbosity:
                            self.dot.show()
                            if (((self.verbosity == 2)
                                 and (self.state_count > 0)
                                 and (self.state_count % 100 == 0))
                                    or self.verbosity == 3):
                                print(path)
        return None

    def process_source(self, json_data):
        """ Process the PDF/HTML source file """

        processed = 0
        bill_json = json.loads(json_data)
        detail = BillDetail(bill_json['bill'])

        logger.debug(f"289:detail={detail}")

        # If a bill has multiple versions, choose the latest one.
        if detail.texts:
            earliest_year, chosen = detail.latest_text()
            detail.choose_document(chosen)

            if self.fromyear <= int(detail.doc_date[:4]):

                # Generate the key to be used to refer to this legislation.
                key = self.fobhelp.bill_text_key(detail.state,
                                                 detail.bill_number,
                                                 detail.session_id,
                                                 earliest_year)
                detail.key = key

                if (self.after is None) or (self.after < key):

                    self.process_detail(detail)
                    # If we already have extracted the text file,
                    # honor the --skip parameter
                    text_name = self.fobhelp.bill_text_name(key, "txt")
                    processed = self.skip_if_exists(text_name, detail)
            else:
                logger.debug(f"312:Too old, skipping: {detail.doc_date}")

        else:
            logger.warning(f"318:No texts found for {detail.state}-"
                           f"{detail.bill_number}-"
                           f"{detail.session_id}")

        return processed

    def process_detail(self, detail):
        """ Process bill detail """

        detail.title = titlecase(detail.title)

        law_record = Law.objects.filter(key=detail.key)
        if law_record is None:
            logger.debug(f"366:Creating LAW record: {detail.key}")
            law_record = Law(key=detail.key, title=detail.title,
                             summary=detail.summary, bill_id=detail.bill_id,
                             location=self.loc, doc_date=detail.doc_date)
            law_record.save()
        else:
            logger.debug(f"302:LAW record already exists: {detail.key}")

        return None

    def skip_if_exists(self, text_name, detail):
        """ check if file exists """

        skipping = False
        processed = 0
        if self.fob.item_exists(text_name):
            if self.skip:
                skip_msg = f"File {text_name} already exists, skipping"
                logger.debug(f"381:SKIP {skip_msg}")
                if self.verbosity > 2:
                    print(skip_msg)
                elif self.verbosity:
                    self.dot.show(char='>')
                processed = 0
                skipping = True
            else:
                textdata = self.fob.download_text(text_name)
                headers = Oneline.Oneline_parse_header(textdata)
                if ('CITE' in headers
                        and headers['CITE'][:8] != 'Legiscan'
                        and headers['CITE'][-7:] != 'general'):
                    detail.cite_url = headers['CITE']
                    logger.debug(f"327:OLD CITE_URL={detail.cite_url}")
                elif (('CITE' in headers)
                      and (headers['CITE'][:8] == 'Legiscan')):
                    detail.cite_url = detail.url
                    logger.debug(f"334:NEW CITE_URL={detail.cite_url}")

        if not skipping:
            processed = self.process_bill(detail)

        return processed

    def process_bill(self, detail):
        """ process individual PDF/HTML bill """

        key = detail.key
        detail.bill_name = self.fobhelp.bill_text_name(key, detail.extension)
        bill_hash = Hash.find_item_name(detail.bill_name)
        logger.debug(f"345:bill_name={detail.bill_name} bill_hash={bill_hash}")

        # If the source PDF/HTML exists, and the hash code matches,
        # then it is up-to-date and we can use it directly.
        fob_source = False
        if (self.fob.item_exists(detail.bill_name)
                and bill_hash is not None
                and bill_hash.hashcode == detail.hashcode):
            # read the existing PDF/HTML file we have in File/Object store
            fob_source = True

        processed = 0
        bindata = None
        source_file = detail.bill_name

        if fob_source:
            logger.debug(f"361:Reading existing: {detail.bill_name}")
            bindata = self.fob.download_binary(detail.bill_name)
            source_file = "{} ({})".format(detail.bill_name,
                                           settings.FOB_METHOD)
        else:
            logger.debug(f"414:Fetch from state: {detail.bill_name}")
            bindata = self.fetch_state_link(detail)

        # For HTML, convert to text.  Othewise leave binary for PDF.
        if bindata and detail.extension == 'html':
            textdata = bindata.decode('UTF-8', errors='ignore')
            self.process_html(key, detail, textdata)
            processed = 1
        elif bindata and detail.extension == 'pdf':
            self.process_pdf(detail, bindata)
            processed = 1

        # If successful, save the hash code to the cfc_app_hash table
        if processed:
            save_source_hash(bill_hash, detail)
            self.dot.show()
        else:
            logger.error(f"435:Failure processing source: {source_file}")
        return processed

    def fetch_state_link(self, detail):
        """ Fetch PDF/HTML from State Link or Legiscan.com API """

        bindata = b''
        bill_bundle = DataBundle(detail.bill_name)

        baseurl, params = detail.parse_url()

        response = bill_bundle.make_request(baseurl, params)
        result = bill_bundle.load_response(response)
        # import pdb; pdb.set_trace()
        if result:
            bindata = bill_bundle.content
            if ((detail.extension == "pdf")
                    and (bindata[:4] != b'%PDF')):
                logger.error(f"392:Invalid PDF format found: "
                             f"{detail.bill_name}")
                bindata = None

        if bindata:
            self.fob.upload_binary(bindata, detail.bill_name)
            detail.cite_url = detail.state_link
            saving_msg = f"Saving file: {detail.bill_name}"
            logger.debug(f"398: {saving_msg}")
            if self.verbosity > 2:
                print(saving_msg)

        elif self.api_limit > 0 and self.leg.api_ok:
            bindata = self.fetch_legiscan_api(detail)

        return bindata

    def fetch_legiscan_api(self, detail):
        """ Fetch from Legiscan API using getBillText command """

        bindata = b""
        logger.warning(f"403:Invoking Legiscan API: {detail.bill_name} "
                       f"doc_id={detail.doc_id}")
        response = self.leg.get_bill_text(detail.doc_id)
        detail.cite_url = detail.url
        self.api_limit -= 1
        if response:
            json_data = json.loads(response)
            json_text = json_data['text']
            json_doc = json_text['doc']
            mimedata = json_doc.encode('UTF-8')
            bindata = base64.b64decode(mimedata)

        return bindata

    def process_html(self, key, detail, billtext):
        """ Process HTML source file of legislation """

        text_name = self.fobhelp.bill_text_name(key, 'txt')

        text_line = Oneline(nltk_loaded=True)
        Oneline_add_header(text_line, detail)

        self.parse_html(billtext, text_line)
        self.write_file(text_line, text_name)

        return self

    def write_file(self, text_line, text_name):
        """ Write text file as series of full sentences  """

        text_line.split_sentences()
        logger.info(f"478:Writing: {text_name}")
        self.fob.upload_text(text_line.oneline, text_name)
        return

    def process_pdf(self, detail, msg_bytes):
        """ Parse PDF file to extract text """

        logger.debug(f"485:key={detail.key}")
        input_str = ""

        detail.bill_name = self.fobhelp.bill_text_name(detail.key, 'pdf')
        miner = PDFtoText(detail.bill_name, msg_bytes)
        input_str = miner.convert_to_text()

        if input_str:
            text_name = self.fobhelp.bill_text_name(detail.key, 'txt')
            text_line = Oneline(nltk_loaded=True)
            Oneline_add_header(text_line, detail)
            self.parse_intermediate(input_str, text_line)
            self.write_file(text_line, text_name)

        return self

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
            extension = BillDetail.determine_extension(mime_type)

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

# end of module
