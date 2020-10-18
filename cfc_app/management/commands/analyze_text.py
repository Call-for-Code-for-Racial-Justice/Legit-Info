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
#
# If you leave out the --api, the IBM Watson NLU API will not be invoked,
# this is useful to process TXT files using just the wordmap.csv file.
#
import os
import sys
import glob
import re
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import pandas as pd
import numpy as np
import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from ibm_watson.natural_language_understanding_v1 import (Features, 
EmotionOptions, SentimentOptions, SemanticRolesOptions,KeywordsOptions,
ConceptsOptions,SemanticRolesOptions,SyntaxOptions,SyntaxOptionsTokens,
CategoriesOptions,ConceptsOptions)

from django.core.management.base import BaseCommand
from django.conf import settings

from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.models import Location, Impact, Law
from cfc_app.ShowProgress import ShowProgress


# Constants for IBM Watson NLU credentials in Environment Variables
NLU_APIKEY = os.environ['NLU_APIKEY']
NLU_SERVICE_URL = os.environ['NLU_SERVICE_URL']

NameRegex = re.compile(r"^(\w\w-\w*-Y\d*).")
HeadRegex = re.compile(r"^(\w\w-\w*-Y\d*).\w*\s(\d\d\d\d-\d\d-\d\d)\s*_TITLE_\s*(.*)_SUMMARY_\s*(.*)_TEXT_")
keyRegex = re.compile(r"^\w\w-(.*)-")

class Command(BaseCommand):
    help =  'For all text files found in File/Object storage, run the'
    help += 'IBM Watson Natural Language Understanding (NLU) API, generate '
    help += 'relevant words or phrases, and compare these to the '
    help += 'wordmap.csv table determine the impact of each legislation.'
    help += 'The wordmap.csv is stored in the /sources directory as part '
    help += 'this application project.'


    def add_arguments(self, parser):
        parser.add_argument("--api", action="store_true",
                            help="Invoke IBM Watson NLU API")
        parser.add_argument("--state", help="Process single state: AZ, OH")
        parser.add_argument("--limit", type=int, default=0, 
                            help="Limit number of entries to detail")

        return self


    def handle(self, *args, **options):

        impacts = Impact.objects.all().exclude(text='None')
        impact_list = []
        for imp in impacts:
            impact_list.append(imp.text)
        wordmap = self.load_wordmap(impact_list)

        limit = 0
        if options['limit']:
            limit = options['limit']

        usa = Location.objects.get(shortname='usa')
        locations = Location.objects.order_by('hierarchy').filter(parent=usa)
        for loc in locations:
            state = loc.shortname.upper()  # Convert state to UPPER CASE
            if options['state']:
                if state != options['state']:
                    continue

            print('Analyzing state: {} -- {}'.format(state,loc.desc))
            self.process_state(state, wordmap, limit)
        return None


    def process_state(self, state, wordmap, limit):
        # import pdb; pdb.set_trace()
        fob = FOB_Storage(settings.FOB_METHOD)

        json_str = fob.download_text('{}.json'.format(state))
        json_data = json.loads(json_str)

        handles =  fob.list_handles(prefix=state, suffix=".txt", limit=limit)



        dot = ShowProgress()
        num = 0
        for filename in handles:
            terms = self.process_legislation(filename, wordmap, json_data)
            dot.show()
            num += 1
            if limit>0 and num >= limit:
                break
        dot.end()
        return None


    # returns top 5 impact areas from 
    # the text extracted from bills
    def ImpactAreaFromBill(self, text):    
    
    # http://watson-developer-cloud.github.io/python-sdk/v3.0.2/apis/ibm_watson.natural_language_understanding_v1.html

        authenticator = IAMAuthenticator(NLU_APIKEY)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2019-07-12',
            authenticator=authenticator
            )

        natural_language_understanding.set_service_url(NLU_SERVICE_URL)

        tokens = SyntaxOptionsTokens(lemma=True, part_of_speech=True)
        syntax = SyntaxOptions(tokens=tokens, sentences=True)
        features = Features(categories=CategoriesOptions(limit=5),
                sentiment=SentimentOptions(),concepts=ConceptsOptions(limit=5),
                keywords=KeywordsOptions(sentiment=True,limit=10),
                syntax=syntax)
   
        response = natural_language_understanding.analyze(features, text=text,
                language='en')

        result = response.get_result()
        concept=result.get("concepts")
        return concept


    def process_legislation(self, filename, wordmap, json_data):
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
        relevant_words = self.ImpactAreaFromBill(extracted_text) 
        revlist, impact_chosen = self.classify_impact(relevant_words, wordmap)

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
        wordmap = {}
        mapname = os.path.join(settings.SOURCE_ROOT, 'wordmap.csv')
        with open(mapname, 'r') as mapfile:
            maplines = mapfile.readlines()
        
        for line in maplines:
            columns = line.split(',')
            term, impact_category = columns[0].strip(), columns[1].strip()
            if term =='term' or impact_category == 'impact':
                continue
            if impact_category.upper() in ['NONE', 'REMOVE']:
                continue
            if impact_category in impact_list:
                wordmap[term] = impact_category
        return wordmap


    def classify_impact(self, terms, wordmap):

        RelForm = "'{}' ==> '{}'"
        
        impact_chosen = 'None'
        revlist = []
        for rel in terms:
            term = rel['text'].strip()
            if term in wordmap:
                revlist.append([term, wordmap[term]])
            else:
                revlist.append([term, 'None'])

        # Choose the most relevant impact.
        for rel in revlist:
            impact = rel[1]
            if impact_chosen == 'None':
                impact_chosen = impact

        return revlist, impact_chosen

