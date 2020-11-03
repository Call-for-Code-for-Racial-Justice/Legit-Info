#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scan TXT files, assign Impact, save into cfc_app_law database.

This is phase 3 of weekly cron job.  See CRON.md for details.
Invoke with ./stage1 get_datasets  or ./cron1 get_datasets
Specify --help for details on parameters available.

The IBM Watson Natural Language Understanding API is used for this.
See http://watson-developer-cloud.github.io/python-sdk/v3.0.2/apis/
         ibm_watson.natural_language_understanding_v1.html for details.

If you leave out the --api, the IBM Watson NLU API will not be invoked,
this is useful to process TXT files using just the wordmap.csv file.

Written Shilpi Bhattacharyya and Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging
import os
import re

# Django and other third-party imports
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

import ibm_watson.natural_language_understanding_v1 as NLU

# Application imports
from cfc_app.fob_storage import FOB_Storage
from cfc_app.legiscan_api import LEGISCAN_ID
from cfc_app.log_time import LogTime
from cfc_app.models import Location, Impact, Law
from cfc_app.Oneline import Oneline
from cfc_app.show_progress import ShowProgress
from cfc_app.word_map import WordMap

# Debug with:  import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

# Constants for IBM Watson NLU credentials in Environment Variables
NLU_APIKEY = os.getenv('NLU_APIKEY', None)
NLU_SERVICE_URL = os.getenv('NLU_SERVICE_URL', None)

NameRegex = re.compile(r"^(\w\w-\w*-Y\d*).")
keyRegex = re.compile(r"^\w\w-(.*)-")
mapRegex = re.compile(r'["](.*)["]\s*,\s*["](.*)["]')

RLIMIT = 10   # number of phrases to be returned by IBM Watson NLU


class AnalyzeTextError(CommandError):
    """ customized error for this command. """
    pass


class Command(BaseCommand):
    """ Command handler for analyze_text """

    help = ("For all text files found in File/Object storage, run the "
            "IBM Watson Natural Language Understanding (NLU) API, generate "
            "relevant words or phrases, and compare these to the "
            "'wordmap.csv' table determine the impact of each legislation."
            "The wordmap.csv is stored in the /sources directory as part "
            "this application.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.impact_list = None
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.wordmap = None
        self.use_api = False
        self.after = None
        self.limit = 10
        self.rel_start = '(MAP)'

        state_id_table = {}
        for state_id in LEGISCAN_ID:
            state = LEGISCAN_ID[state_id]['code']
            state_id_table[state] = state_id
        self.id_table = state_id_table

        self.verbosity = 1
        return None

    def add_arguments(self, parser):
        """ add arguments for parsing """

        parser.add_argument("--api", action="store_true",
                            help="Invoke IBM Watson NLU API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--after", help="Start after this item name")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="number of entries to analyze per state")

        return None

    def handle(self, *args, **options):
        """ handle analyze_text command """

        timing = LogTime("analyze_text")
        timing.start_time(options['verbosity'])

        if options['after']:
            self.after = options['after']

        self.limit = options['limit']

        if options['api']:
            self.use_api = True
            self.rel_start = '(NLU)'
            logger.info('118:Analyzing with IBM Watson NLU API')
        else:
            logger.info('120:Analyzing with internal Wordmap ONLY')

        self.verbosity = options['verbosity']

        impacts = Impact.objects.all().exclude(text='None')
        impact_list = []
        for imp in impacts:
            impact_list.append(imp.text)
        self.impact_list = impact_list

        self.wordmap = WordMap()

        locations = Location.objects.filter(legiscan_id__gt=0)
        locations = locations.order_by('hierarchy')
        for loc in locations:
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            if options['state']:
                if state != options['state']:
                    continue

            logger.info(f"150:Processing: {loc.desc} ({state})")
            # import pdb; pdb.set_trace()
            print("Processing: {} ({})".format(loc.desc, state))
            try:
                self.process_state(state)
            except Exception as exc:
                err_msg = f"151:Process State Error: {exc}"
                logger.error(err_msg, exc_info=True)
                raise AnalyzeTextError(err_msg) from exc

        timing.start_time(options['verbosity'])
        return None

    def process_state(self, state):
        """ process specific state of United States """

        cursor = self.after
        items = self.fob.list_items(prefix=state, suffix=".txt",
                                    after=cursor, limit=0)

        dot = ShowProgress()
        num = 0
        items.sort()
        for filename in items:
            textdata = self.fob.download_text(filename)

            header = Oneline.parse_header(textdata)
            if 'BILLID' in header:
                bill_id = header['BILLID']
                logger.debug(f"231:bill_id={bill_id}")
                self.process_legislation(filename, textdata, header)
                if self.verbosity:
                    dot.show()
                num += 1
                if self.limit > 0 and num >= self.limit:
                    break
            else:
                logger.info(f"238:No bill_id found, removing: {filename}")
                self.fob.remove_item(filename)
                continue

        dot.end()
        return None

    def process_legislation(self, filename, extracted_lines, header):
        """ Process individual bill """

        extracted_text = Oneline.join_lines(extracted_lines)
        extracted_text = extracted_text.replace('"', r'|').replace("'", r"|")

        concept = {}
        if self.use_api:
            logger.debug(f"255:Filename {filename} Concept:{concept}")
            try:
                concept = self.Relevance_NLU(extracted_text)
            except Exception as exc:
                logger.error(f"IBM Watson NLU failed, disabling --api: {exc}")
                self.use_api = False
        else:
            concept = self.wordmap.Relevance(extracted_text)

        if concept:
            self.save_relevance(filename, header, concept)

        return None

    @staticmethod
    def Relevance_NLU(text):
        """ return top impact areas from extracted text using Watson NLU """

        authenticator = IAMAuthenticator(NLU_APIKEY)
        nlup = NaturalLanguageUnderstandingV1(
            version='2019-07-12', authenticator=authenticator)

        nlup.set_service_url(NLU_SERVICE_URL)

        tokens = NLU.SyntaxOptionsTokens(lemma=True, part_of_speech=True)
        syntax = NLU.SyntaxOptions(tokens=tokens, sentences=True)
        features = NLU.Features(categories=NLU.CategoriesOptions(limit=RLIMIT),
                                sentiment=NLU.SentimentOptions(),
                                concepts=NLU.ConceptsOptions(limit=RLIMIT),
                                keywords=NLU.KeywordsOptions(sentiment=True,
                                                             limit=10),
                                syntax=syntax)

        response = nlup.analyze(features, text=text, language='en')

        result = response.get_result()
        concept = result.get("concepts")
        return concept

    def save_relevance(self, filename, header, concept):
        """ Save relevant words found for this bill """

        revlist, impact_chosen = self.classify_impact(concept)

        rel, connector = self.rel_start, ''
        for r in revlist:
            rel += connector + "'{}' => '{}'".format(r[0], r[1])
            connector = ", "

        log_msg = "351:Filename {filename} Impact={impact_chosen} Rel:{rel}"
        logger.debug(log_msg)

        key = filename.replace(".txt", "")

        if self.verbosity > 1:
            print(f"Analyzed filename: {filename} "
                  f"Impact chosen={impact_chosen}")

        self.save_law(key, header, rel, impact_chosen)
        return None

    def classify_impact(self, concept):
        """ Classify the impact based on relevant terms """

        impact_chosen = 'None'
        revlist = []
        for rel in concept:
            term = rel['text'].strip()
            if term in self.wordmap:
                revlist.append([term, self.wordmap[term]])
            else:
                revlist.append([term, 'Unknown'])

        # Choose the most relevant impact.
        for rel in revlist:
            impact = rel[1]
            if impact_chosen not in self.impact_list:
                impact_chosen = impact

        if impact_chosen not in self.impact_list:
            impact_chosen = 'None'

        return revlist, impact_chosen

    def save_law(self, key, header, rel, impact_chosen):
        """ Save the results in cfc_app_law database table """

        # If record exists, check if this is newer..
        doc_date = header['DOCDATE']
        # import pdb; pdb.set_trace()
        if Law.objects.filter(key=key).exists():
            law = Law.objects.get(key=key)
            # import pdb; pdb.set_trace()

            # If the record is up-to-date, leave it alone
            if (law.doc_date
                    and doc_date < law.doc_date):
                logger.debug(f"396:Law left alone {key} "
                             f"Existing={law.impact} Chosen={impact_chosen}")
                return None

            result = 'Updated'
        # otherwise, this is a new record.
        else:
            law = Law()
            law.key = key
            result = 'Created'

        law.bill_id = header['BILLID']
        law.doc_date = doc_date
        law.title = header['TITLE']
        law.summary = header['SUMMARY']

        state = key[:2]
        if state in self.id_table:
            state_id = self.id_table[state]
            if state_id:
                loc = Location.objects.get(legiscan_id=state_id)
                law.location = loc

        imp = Impact.objects.get(text=impact_chosen)
        law.impact = imp

        law.relevance = rel
        if 'CITE' in header:
            law.cite_url = header['CITE']
        law.save()

        logger.info(f"390:Database record {result} for {key}")
        return None

# End of module
