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
from cfc_app.fob_storage import FobStorage
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


RLIMIT = 10   # number of phrases to be returned by IBM Watson NLU
NLUST = "(NLU)"
MAPST = "(MAP)"
BOTH_REGEX = re.compile("[(]NLU[)](.*)[(]MAP[)](.*)")
NLU_REGEX = re.compile("[(]NLU[)](.*)")
MAP_REGEX = re.compile("[(]MAP[)](.*)")


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
        self.fob = FobStorage(settings.FOB_METHOD)
        self.womp = None
        self.use_api = False
        self.after = None
        self.limit = 10
        state_id_table = {}
        for state_id in LEGISCAN_ID:
            state = LEGISCAN_ID[state_id]['code']
            state_id_table[state] = state_id
        self.id_table = state_id_table

        self.verbosity = 1
        self.skip = False
        self.compare = False
        self.count = 0
        return None

    def add_arguments(self, parser):
        """ add arguments for parsing """

        parser.add_argument("--api", action="store_true",
                            help="Invoke IBM Watson NLU API")
        parser.add_argument("--skip", action="store_true",
                            help="Skip if NLU relevance already exists")
        parser.add_argument("--compare", action="store_true",
                            help="Compare NLU and MAP analyses")
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

        if options['skip']:
            self.skip = True

        if options['compare']:
            self.compare = True

        self.limit = options['limit']

        if options['api']:
            self.use_api = True

        self.verbosity = options['verbosity']
        logger.debug(f"134:Options {options}")

        impacts = Impact.objects.all().exclude(iname='None')
        impact_list = []
        for imp in impacts:
            impact_list.append(imp.iname)
        self.impact_list = impact_list

        self.womp = WordMap(RLIMIT)
        self.womp.load_csv(impact_list)

        locations = Location.objects.filter(legiscan_id__gt=0)
        locations = locations.order_by('hierarchy')
        for loc in locations:
            state_id = loc.legiscan_id
            if state_id > 0:
                state = LEGISCAN_ID[state_id]['code']

            if options['state']:
                if state != options['state']:
                    continue

            logger.info(f"150:Processing: {loc.longname} ({state})")
            # import pdb; pdb.set_trace()
            print("Processing: {} ({})".format(loc.longname, state))
            try:
                self.process_state(state)
            except Exception as exc:
                err_msg = f"151:Process State Error: {exc}"
                logger.error(err_msg, exc_info=True)
                raise AnalyzeTextError(err_msg) from exc

        timing.end_time(options['verbosity'])
        return None

    def process_state(self, state):
        """ process specific state of United States """

        cursor = self.after
        items = self.fob.list_items(prefix=state, suffix=".txt",
                                    after=cursor, limit=0)

        dot = ShowProgress()
        self.count = 0
        items.sort()
        for filename in items:
            textdata = self.fob.download_text(filename)

            header = Oneline.Oneline_parse_header(textdata)
            if 'BILLID' in header:
                bill_id = header['BILLID']
                logger.debug(f"231:bill_id={bill_id} {filename}")
                self.process_legislation(filename, textdata, header)
                if self.verbosity:
                    dot.show()
                if self.limit > 0 and self.count >= self.limit:
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

        skipping = False
        key = filename.replace(".txt", "")
        impact_nlu, impact_map = "", ""
        rel_nlu, rel_map = "", ""
        if self.skip or self.compare:
            logger.debug(f"212:Reading {key}")
            law = None
            laws = Law.objects.filter(key=key)
            if laws is not None and len(laws)>0:
                law = laws[0]
            if (law is not None
                    and (law.impact is not None)
                    and law.relevance is not None):
                mop1 = BOTH_REGEX.search(law.relevance)
                mop2 = NLU_REGEX.search(law.relevance)
                mop3 = MAP_REGEX.search(law.relevance)
                if mop1:
                    rel_nlu = NLUST + mop1.group(1)
                    rel_map = MAPST + mop1.group(2)
                    impact_nlu = law.impact.iname
                    impact_map = law.impact.iname
                elif mop2:
                    rel_nlu = NLUST + mop2.group(1)
                    impact_nlu = law.impact.iname
                elif mop3:
                    rel_map = MAPST + mop3.group(1)
                    impact_map = law.impact.iname
                if self.skip and (impact_nlu != ""):
                    logger.debug(f"209:Skipping {filename}")
                    skipping = True

        if not skipping:
            self.count += 1
            if self.use_api:
                try:
                    concept_nlu = self.relevance_nlu(extracted_text)
                    revlist, impact_nlu = self.classify_impact(concept_nlu)
                    rel_nlu = self.format_rel(NLUST, revlist)
                except Exception as exc:
                    logger.error(f"IBM Watson NLU failed, "
                                 f"disabling --api: {exc}")
                    self.use_api = False

            if (not self.use_api) or self.compare:
                concept_map = self.womp.relevance(extracted_text)
                revlist, impact_map = self.classify_impact(concept_map)
                rel_map = self.format_rel(MAPST, revlist)

            rel = rel_nlu + rel_map
            if (impact_nlu not in ["", "None"]
                    and (impact_map not in ["", "None"])):
                if impact_nlu != impact_map:
                    logger.debug(f"254:Impacts don't match {filename} "
                                 f"NLU={impact_nlu} MAP={impact_map}")
                else:
                    logger.debug(f"257:Impacts match {filename} "
                                 f"NLU={impact_nlu} MAP={impact_map}")
            if impact_nlu != "":
                imp_chosen = impact_nlu
            elif impact_map != "":
                imp_chosen = impact_map
            else:
                imp_chosen = "None"

            if rel:
                logger.debug(f"229:Filename {filename} Impact={imp_chosen}")
                self.save_law(key, header, rel, imp_chosen)

        return None

    @staticmethod
    def relevance_nlu(text):
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

    def format_rel(self, rel_start, revlist):
        """ Save relevant words found for this bill """

        rel, connector = rel_start, ''
        for rev in revlist:
            rel += connector + "'{}' => '{}'".format(rev[0], rev[1])
            if rev[1] == "Unknown":
                logger.debug(f'304:"{rev[0]}", "{rev[1]}"')
            connector = ", "

        logger.debug(f"303:{rel_start}: {rel}")

        return rel

    def classify_impact(self, concept):
        """ Classify the impact based on relevant terms """

        impact_chosen = 'None'
        revlist = []
        w_map = self.womp.wordmap
        for rel in concept:
            term = rel['text'].strip()
            if term in w_map:
                revlist.append([term, w_map[term]])
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
            logger.debug(f'343:"Key={key}"')
            law = Law.objects.get(key=key)
            result = 'Updated'
        # otherwise, this is a new record.
        else:
            law = Law()
            law.key = key
            result = 'Created'

        law.bill_id = header['BILLID']
        law.doc_date = doc_date
        if len(header['TITLE'])>200 or len(header['SUMMARY'])>1000:
            logger.debug(f'358:"Too Long: {header}"')
        law.title = header['TITLE'][:199]
        law.summary = header['SUMMARY'][:999]

        state = key[:2]
        if state in self.id_table:
            state_id = self.id_table[state]
            if state_id:
                loc = Location.objects.get(legiscan_id=state_id)
                law.location = loc

        imp = Impact.objects.get(iname=impact_chosen)
        law.impact = imp

        law.relevance = rel
        if 'CITE' in header:
            law.cite_url = header['CITE']
        law.save()

        logger.info(f"390:Database record {result} for {key}")
        return None

# End of module
