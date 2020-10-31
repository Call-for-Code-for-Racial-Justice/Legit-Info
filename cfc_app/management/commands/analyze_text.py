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

from ibm_watson.natural_language_understanding_v1 import (Features,
                                                          SentimentOptions,
                                                          KeywordsOptions,
                                                          ConceptsOptions,
                                                          SyntaxOptions,
                                                          SyntaxOptionsTokens,
                                                          CategoriesOptions)

# Application imports
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.LegiscanAPI import LEGISCAN_ID
from cfc_app.models import Location, Impact, Law
from cfc_app.ShowProgress import ShowProgress
from cfc_app.Oneline import Oneline

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
    pass


class Command(BaseCommand):

    help = ("For all text files found in File/Object storage, run the "
            "IBM Watson Natural Language Understanding (NLU) API, generate "
            "relevant words or phrases, and compare these to the "
            "'wordmap.csv' table determine the impact of each legislation."
            "The wordmap.csv is stored in the /sources directory as part "
            "this application.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.impact_list = None
        self.wordmap = None
        self.secondary_impacts = None
        self.primray = None
        self.secondary = None
        self.tertiary = None

        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.use_api = False
        self.after = None
        self.limit = 10
        self.rel_start = '(MAP)'

        state_id_table = {}
        for state_id in LEGISCAN_ID:
            state = LEGISCAN_ID[state_id]['code']
            state_id_table[state] = state_id
        self.id_table = state_id_table
        return None

    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke IBM Watson NLU API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--after", help="Start after this item name")
        parser.add_argument("--limit", type=int, default=self.limit,
                            help="number of entries to analyze per state")

        return None

    def handle(self, *args, **options):

        if options['after']:
            self.after = options['after']

        self.limit = options['limit']

        if options['api']:
            self.use_api = True
            self.rel_start = '(NLU)'
            logger.info('Analyzing with IBM Watson NLU API')
        else:
            logger.info('Analyzing with internal Wordmap ONLY')

        impacts = Impact.objects.all().exclude(text='None')
        impact_list = []
        for imp in impacts:
            impact_list.append(imp.text)
        self.impact_list = impact_list

        try:
            self.load_wordmap(impact_list)
        except Exception as e:
            err_msg = "133:Load Wordmap: {}".format(e)
            logger.error(err_msg, exc_info=True)
            raise AnalyzeTextError(err_msg)

        locations = Location.objects.filter(legiscan_id__gt=0)
        locations = locations.order_by('hierarchy')
        for loc in locations:
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            if options['state']:
                if state != options['state']:
                    continue

            logger.info('153:Processing: {} ({})'.format(loc.desc, state))
            import pdb; pdb.set_trace()
            try:
                self.process_state(state)
            except Exception as e:
                err_msg = "158:Process State Error {}".format(e)
                logger.error(err_msg, exc_info=True)
                raise AnalyzeTextError(err_msg)

        return None

    def load_wordmap(self, impact_list):
        wordmap, categories = {}, []
        mapname = os.path.join(settings.SOURCE_ROOT, 'wordmap.csv')
        print(mapname)

        with open(mapname, 'r') as mapfile:
            maplines = mapfile.readlines()

        print(len(maplines))
        for line in maplines:
            mo = mapRegex.search(line)
            if mo:
                term = mo.group(1).strip()
                impact_category = mo.group(2).strip()
                if term == 'term' or impact_category == 'impact':
                    continue
                if impact_category.upper() in ['REMOVE']:
                    continue
                if impact_category.upper() in ['NONE']:
                    impact_category = 'None'
                wordmap[term] = impact_category
                if impact_category not in categories:
                    categories.append(impact_category)
            else:
                print("Regex Error", line)

        print('Impacts marked with * match cfc_app_impact table')
        secondary_list = []
        for impact in categories:
            marker = ' '
            if impact in impact_list:
                marker = '*'
            elif impact != 'None':
                secondary_list.append(impact)
            print(marker, impact)

        self.wordmap = wordmap
        self.secondary_impacts = secondary_list

        primary, secondary, tertiary = [], [], []
        for term in wordmap:
            if wordmap[term] in impact_list:
                primary.append([term, wordmap[term]])
            elif wordmap[term] in secondary_list:
                secondary.append([term, wordmap[term]])
            else:
                tertiary.append([term, wordmap[term]])

        status_msg = '{}: {}, with {} terms'
        logger.debug(status_msg.format("Primary", primary, len(primary)))
        logger.debug(status_msg.format("Secondary", secondary, len(secondary)))
        logger.debug(status_msg.format("Tertiary", tertiary, len(tertiary)))

        self.primary = primary
        self.secondary = secondary
        self.tertiary = tertiary
        return None

    def process_state(self, state):
        # import pdb; pdb.set_trace()

        cursor = self.after
        items = self.fob.list_items(prefix=state, suffix=".txt",
                                    after=cursor, limit=0)

        dot = ShowProgress()
        num = 0
        items.sort()
        for filename in items:
            textdata = self.fob.download_text(filename)
            import pdb; pdb.set_trace()
            header = Oneline.parse_header(textdata)
            if 'BILLID' in header:
                bill_id = header['BILLID']
                logger.debug("166:bill_id={}".format(bill_id))
                self.process_legislation(filename, textdata, header)
                dot.show()
                num += 1
                if self.limit > 0 and num >= self.limit:
                    break
            else:
                logger.info('No bill_id found in header, removing: ', filename)
                self.fob.remove_item(filename)
                continue

        dot.end()
        return None

    def process_legislation(self, filename, extracted_lines, header):

        extracted_text = Oneline.join_lines(extracted_lines)
        extracted_text = extracted_text.replace('"', r'|').replace("'", r"|")

        if self.use_api:
            concept = self.Relevance_NLU(extracted_text)
        else:
            concept = self.Relevance_Wordmap(extracted_text)

        revlist, impact_chosen = self.classify_impact(concept)

        rel, connector = self.rel_start, ''
        for r in revlist:
            rel += connector + "'{}' => '{}'".format(r[0], r[1])
            connector = ", "

        print('Filename {}  Impact {}'.format(filename, impact_chosen))

        key = filename.replace(".txt", "")
        self.save_law(key, header, rel, impact_chosen)

        return None

    def Relevance_NLU(self, text):
        """ return top impact areas from extracted text using Watson NLU """

        authenticator = IAMAuthenticator(NLU_APIKEY)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2019-07-12',
            authenticator=authenticator
        )

        natural_language_understanding.set_service_url(NLU_SERVICE_URL)

        tokens = SyntaxOptionsTokens(lemma=True, part_of_speech=True)
        syntax = SyntaxOptions(tokens=tokens, sentences=True)
        features = Features(categories=CategoriesOptions(limit=RLIMIT),
                            sentiment=SentimentOptions(),
                            concepts=ConceptsOptions(limit=RLIMIT),
                            keywords=KeywordsOptions(sentiment=True, limit=10),
                            syntax=syntax)

        response = natural_language_understanding.analyze(features, text=text,
                                                          language='en')

        result = response.get_result()
        concept = result.get("concepts")
        return concept

    def Relevance_Wordmap(self, extracted_text):
        """ return top impact areas from extracted text using Wordmap """
        concept = []

        self.scan_extract(extracted_text, self.primary, concept)
        if len(concept) < RLIMIT:
            self.scan_extract(extracted_text, self.secondary, concept)
        if len(concept) < RLIMIT:
            self.scan_extract(extracted_text, self.tertiary, concept)

        return concept

    def scan_extract(self, extracted_text, category_list, concept):
        for rel in category_list:
            term = rel[0]
            if term in extracted_text:
                concept.append({'text': term, 'Reason': self.wordmap[term]})
                if len(concept) >= RLIMIT:
                    break
        return None

    def classify_impact(self, concept):
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

        # If record exists, check if this is newer..
        doc_date = header['DOCDATE']
        # import pdb; pdb.set_trace()
        if Law.objects.filter(key=key).exists():
            law = Law.objects.get(key=key)
            # import pdb; pdb.set_trace()

            # If the record is up-to-date and matches the
            # impact chosen, leave it alone
            if (law.doc_date
                    and doc_date < law.doc_date
                    and impact_chosen == law.impact.text):
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
        law.cite_url = header['CITE']
        law.save()

        print('Database record {} for {}'.format(result, key))
        return None

# End of module
