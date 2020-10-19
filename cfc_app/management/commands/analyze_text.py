# Python Code
# analyze_text.py -- Scan TXT files, assign Impact, Save into Django Database
# By Shilpi Bhattacharyya and Tony Pearson, IBM, 2020
# Requires: pip install -U ibm-cos-sdk ibm-watson
#
# This is intended as a background task
#
# You can invoke this in either "on demand" or as part of a "cron" job
#
# On Demand:
# [...] $ pipenv shell
# (cfc) $ ./stage1 analyze_text --api --state AZ --limit 10
#
# Cron Job:
# /home/yourname/Develop/legit-info/cron1 anallyze_text --api --limit 10
#
# The IBM Watson Natural Language Understanding API is used for this.
# See http://watson-developer-cloud.github.io/python-sdk/v3.0.2/apis/
#     ibm_watson.natural_language_understanding_v1.html for details.
#
# If you leave out the --api, the IBM Watson NLU API will not be invoked,
# this is useful to process TXT files using just the wordmap.csv file.
#

import os
import re
import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from ibm_watson.natural_language_understanding_v1 import (Features,
                                                          SentimentOptions,
                                                          KeywordsOptions,
                                                          ConceptsOptions,
                                                          SyntaxOptions,
                                                          SyntaxOptionsTokens,
                                                          CategoriesOptions)

from django.core.management.base import BaseCommand
from django.conf import settings

from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.models import Location, Impact, Law
from cfc_app.ShowProgress import ShowProgress


# Constants for IBM Watson NLU credentials in Environment Variables
NLU_APIKEY = os.environ['NLU_APIKEY']
NLU_SERVICE_URL = os.environ['NLU_SERVICE_URL']

NameRegex = re.compile(r"^(\w\w-\w*-Y\d*).")
HeadRegex1 = r"^(\w\w-\w*-Y\d*).\w*\s(\d\d\d\d-\d\d-\d\d)\s*"
HeadRegex2 = r"_TITLE_\s*(.*)_SUMMARY_\s*(.*)_TEXT_"
HeadRegex = re.compile(HeadRegex1+HeadRegex2)
keyRegex = re.compile(r"^\w\w-(.*)-")
mapRegex = re.compile(r'["](.*)["]\s*,\s*["](.*)["]')


class Command(BaseCommand):

    help = 'For all text files found in File/Object storage, run the'
    help += 'IBM Watson Natural Language Understanding (NLU) API, generate '
    help += 'relevant words or phrases, and compare these to the '
    help += 'wordmap.csv table determine the impact of each legislation.'
    help += 'The wordmap.csv is stored in the /sources directory as part '
    help += 'this application project.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        impacts = Impact.objects.all().exclude(text='None')
        impact_list = []
        for imp in impacts:
            impact_list.append(imp.text)
        self.impact_list = impact_list

        wordmap, secondary_impacts = self.load_wordmap(impact_list)
        self.wordmap = wordmap
        self.secondary_impacts = secondary_impacts
        primary, secondary = [], []
        for term in wordmap:
            if wordmap[term] in impact_list:
                primary.append([ term, wordmap[term] ])
            elif wordmap[term] in secondary_impacts:
                secondary.append([ term, wordmap[term] ])
        self.primary = primary
        self.secondary = secondary

        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.use_api = False
        self.limit = 0
        return None


    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke IBM Watson NLU API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=0,
                            help="Limit number of entries to detail")

        return None

    def handle(self, *args, **options):

        if options['limit']:
            self.limit = options['limit']
        if options['api']:
            self.use_api = True

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            if options['state']:
                if state != options['state']:
                    continue

            print('Analyzing state: {} -- {}'.format(state, loc.desc))
            self.process_state(state)
        return None

    def process_state(self, state):
        # import pdb; pdb.set_trace()

        json_str = self.fob.download_text('{}.json'.format(state))
        json_data = json.loads(json_str)

        handles = self.fob.list_handles(prefix=state, suffix=".txt", 
                                        limit=self.limit)

        dot = ShowProgress()
        num = 0
        for filename in handles:
            self.process_legislation(filename, json_data)
            dot.show()
            num += 1
            if self.limit > 0 and num >= self.limit:
                break
        dot.end()
        return None

    # returns top 5 impact areas from
    # the text extracted from bills

    def Relevance_NLU(self, text):

        authenticator = IAMAuthenticator(NLU_APIKEY)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2019-07-12',
            authenticator=authenticator
        )

        natural_language_understanding.set_service_url(NLU_SERVICE_URL)

        tokens = SyntaxOptionsTokens(lemma=True, part_of_speech=True)
        syntax = SyntaxOptions(tokens=tokens, sentences=True)
        features = Features(categories=CategoriesOptions(limit=5),
                            sentiment=SentimentOptions(),
                            concepts=ConceptsOptions(limit=5),
                            keywords=KeywordsOptions(sentiment=True, limit=10),
                            syntax=syntax)

        response = natural_language_understanding.analyze(features, text=text,
                                                          language='en')

        result = response.get_result()
        concept = result.get("concepts")
        return concept

    def Relevance_Map(self, extracted_text):
        return concept

    def process_legislation(self, filename, json_data):
        lob = FOB_Storage(settings.FOB_METHOD)
        key = ''
        mo = NameRegex.search(filename)
        if mo:
            key = mo.group(1)
        doc_date = ''
        title = ''
        summary = ''
        extracted_text = lob.download_text(filename)
        mo = HeadRegex.search(extracted_text)
        if mo:
            if key == '':
                key = mo.group(1)
            doc_date = mo.group(2)
            title = mo.group(3)
            summary = mo.group(4)

        if self.use_api:
            concept = self.Relevance_NLU(extracted_text)
        else:
            concept = self.Relevance_Wordmap(extracted_text)

        revlist, impact_chosen = self.classify_impact(concept)

        if key:
            rel, connector = '', ''
            for r in revlist:
                rel += connector + "'{}' => '{}'".format(r[0], r[1])
                connector = ", "

            bill_id = self.get_bill_id(json_data, key)
            self.save_law(key, bill_id, doc_date, title,
                          summary, rel, impact_chosen)

        return None

    def save_law(self, key, bill_id, doc_date, title,
                 summary, rel, impact_chosen):

        # If record exists, check if this is newer..
        if Law.objects.filter(key=key).exists():
            law = Law.objects.get(key=key)
            if doc_date <= law.doc_date:
                return
            result = 'Updated'
        # otherwise, this is a new record.
        else:
            law = Law()
            law.key = key
            result = 'Created'

        law.bill_id = bill_id
        law.doc_date = doc_date
        law.title = title
        law.summary = summary

        state = key[:2].lower()
        loc = Location.objects.get(shortname=state)
        law.location = loc

        imp = Impact.objects.get(text=impact_chosen)
        law.impact = imp

        law.relevance = rel
        law.save()

        print('Database record {} for {}'.format(result, key))
        return None

    def get_bill_id(self, json_data, key):
        bill_id = ''
        mo = keyRegex.search(key)
        if mo:
            bill_number = mo.group(1)
            for entry in json_data:
                bill = json_data[entry]
                if bill_number == bill['bill_number']:
                    bill_id = bill['bill_id']
                    break

        return bill_id

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
                if impact_category.upper() == 'NONE':
                    impact_category = 'None'
                wordmap[term] = impact_category
                if impact_category not in categories:
                    categories.append(impact_category)
            else:
                print("Regex Error", line)

        print('Impacts marked with * match Django database')
        secondary_list = []
        for impact in categories:
            marker = ' '
            if impact in impact_list:
                marker = '*'
            else:
                secondary_list.append(impact)
            print(marker, impact)

        return wordmap, secondary_list

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

        return revlist, impact_chosen
