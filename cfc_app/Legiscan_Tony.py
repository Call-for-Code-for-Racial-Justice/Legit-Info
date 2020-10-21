#!/usr/bin/env python3
# Legiscan_API.py -- Pull data from Legiscan.com API
# By Uchechukwu Uboh and Tony Pearson, IBM, 2020
#
# Debug with:  # import pdb; pdb.set_trace()


import logging
import json
import os
from random import randint
import requests
from cfc_app.ShowProgress import ShowProgress
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings

"""
    Legiscan_API class automates the retrival and curation of bill data for a
particular US state. Before running this class, your Legiscan.com apikey needs
to be an environmental variable with the key of "LEGISCAN_API_KEY". Visit
https://legiscan.com/legiscan to create your own Legiscan.com apikey.
"""


class LegiscanError(Exception):
    pass


class APIkeyError(LegiscanError):
    pass


class Legiscan_API:

    def __init__(self):
        """Constructor for Legiscan_API.
           Checks if a Legiscan_API apikey exists."""
        self.apiKey = os.getenv('LEGISCAN_API_KEY', None)
        if not self.apiKey:
            raise APIkeyError

        self.badKey = os.getenv('LEGISCAN_BAD_KEY', None)
        self.url = "https://api.legiscan.com/"
        self.api_ok = True    # assume safe to use API
        self.fob = FOB_Storage(settings.FOB_METHOD)
        return None

    def get_dataset_list(self, apikey='Good'):
        """ Get list of datasets for all 50 states """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        list_params = { 'key': key, 'op': 'getDatasetList'} 
        response = invoke_api(list_params)
        
        list_data = response['datasetlist']
        return list_data

    def get_session_id(self, session_id, access_key, apikey='Good'):
        """ Get datasets for individual legislative session """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        sesh_params = { 'key': key, 'op': 'getDataset', 
                        'id': session_id, 'access_key': access_key }

        response = self.invoke_api(sesh_params)
        session_data = response['dataset']
        return session_data

    def invoke_api(self, params):
        """ Invoke the Legiscan API """

        response = {}
        if self.api_ok:
            try:
                response = requests.get(url=self.url, params=params)
                print(response.ok)
                print(response.headers)
                print(response.status_code)
                print(len(response.content), len(response.text)) 
                    
            except Exception as e:
                self.api_ok = False
                resp = response.json()
                if resp:
                    for r in resp:
                        print(r, resp[r])
                # raise LegiscanError
        return resp

    def getBill(self, billID):
        """Return the document id (docID) for a given bill id."""
        docID = None
        LastDate = "0000-00-00"
        if self.api_ok:
            try:
                billdetails = requests.get(self.url + "getBill&id=" + billID)
            except Exception as e:
                self.api_ok = False
                logging.error(
                    "Error: error getting document number. " + str(e))

            billjson = billdetails.json()
            documents = None
            if billjson['status'] == 'OK':
                billinfo = billjson['bill']
                documents = billinfo['texts']
            for doc in documents:
                docDate = doc['date']
                if docDate > LastDate:
                    docID = str(doc['doc_id'])
                    LastDate = docDate

        return docID, LastDate

    def getBillText(self, docID):
        """Return base64 encoded bill text based on given document id."""
        bill_text = ''
        if self.api_ok:
            try:
                response = requests.get(self.url + "getBillText&id=" + docID)
                if 'status' in response:
                    if response['status'] == 'ERROR':
                        self.api_ok = False
                    elif response['status'] == 'OK':
                        package = response.json()
                        bill_text = package['text']
            except Exception as e:
                self.api_ok = False
                logging.error("Error: error getting bill text. " + str(e))

        return bill_text

    def getAllBills(self, state, json_handle, limit=10):
        """Create a json file of all bill for a given state. Each object
            represents a bill and contains bill_id, number, title,
            description, mime, and bill_text."""

        bills, response = {}, {}

        if self.fob.handle_exists(json_handle):
            json_str = self.fob.download_text(json_handle)
            bills = json.loads(json_str)

        if self.api_ok:
            try:
                state_url = self.url + "getMasterList&state=" + state
                stateBills = requests.get(state_url)
                response = stateBills.json()

                # Legiscan imposes a limit of 30,000 requests per month
                # If the limit is exceeded, print message response here.
                if 'status' in response:
                    if response['status'] == 'ERROR':
                        self.api_ok = False
                        print(response['alert'])

            except Exception as e:
                self.api_ok = False
                logging.error("Error: error getting state bills. " + str(e))

        if 'masterlist' in response:
            masterList = response["masterlist"]

            for i in masterList:
                localDict = {}
                if "bill_id" in masterList[i]:
                    localDict["bill_id"] = masterList[i]["bill_id"]
                if "number" in masterList[i]:
                    localDict["bill_number"] = masterList[i]['number']
                if "title" in masterList[i]:
                    localDict["title"] = masterList[i]['title']
                if "description" in masterList[i]:
                    localDict["summary"] = masterList[i]['description']

                # If none of the four above are found, do not add to
                # the list.  Otherwise, add "State" as Location.
                if len(localDict) > 0:
                    localDict["location"] = state
                    bills[len(bills)] = localDict

        num_bills = len(bills)
        if num_bills == 0:
            print('Unable to get latest info from Legiscan.com, ')
            print('and {} contains no entries.'.format(json_handle))
            raise LegiscanError

        dot = ShowProgress()
        session, detail, num = 0, 0, 0

        for entry in bills:
            bill = bills[entry]
            if 'bill_number' in bill:
                session += 1
            if 'doc_id' in bill:
                detail += 1
        print('{}: Entries: {}  Session: {}   Detail: {}'.format(
                json_handle, num_bills, session, detail))

        if self.api_ok:
            # import pdb; pdb.set_trace()
            # We have three scanning modes:
            # Mode 1: Fetch every bill fresh, high limit or unlimited,
            #         getting the latest doc_id and doc_date for all bills.
            if limit == 0 or limit >= num_bills:
                for index in bills:
                    self.fetch_bill(bills, index)
                    dot.show()

            # Mode 2: if limit is placed, only fetch bills that are
            #         missing detail like doc_id and doc_date.
            elif limit > 0 and detail < num_bills:
                for index in bills:
                    if "doc_id" not in bills[index]:
                        self.fetch_bill(bills, index)
                        num += 1
                        dot.show()
                        if num >= limit:
                            break

            # Mode 3: if limit is placed, and all bills have previously
            #         fetched detail, randomly refresh scattered bills.
            elif limit < num_bills:
                for j in range(limit):
                    index = randint(0, num_bills)
                    self.fetch_bill(bills, index)
                    dot.show()
            dot.end()

        textdata = json.dumps(bills)
        self.fob.upload_text(textdata, json_handle)

        print("File {} uploaded".format(json_handle))
        return None

    def fetch_bill(self, bills, index):
        billID = str(bills[index]["bill_id"])
        docID = None
        if self.api_ok:
            try:
                docID, LastDate = self.getBill(billID)
            except Exception as e:
                self.api_ok = False
                logging.error(
                    "Error: error getting document number. " + str(e))

        if docID:
            bills[index]["doc_id"] = docID
            bills[index]["doc_date"] = LastDate
        return None
