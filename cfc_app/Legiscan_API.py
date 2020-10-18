#!/usr/bin/env python3
# Legiscan_API.py -- Pull data from Legiscan.com API
# By Uchechukwu Uboh and Tony Pearson, IBM, 2020
#

import requests
import os
import logging
import sys
import random
from cfc_app.ShowProgress import ShowProgress
from cfc_app.FOB_Storage import FOB_Storage
from django.conf import settings

"""
    Legiscan_API class automates the retrival and curation of bill data for a
particular US state. Before running this class, your Legiscan.com apikey needs
to be an environmental variable with the key of "LEGISCAN_API_KEY". Visit
https://legiscan.com/legiscan to create your own Legiscan.com apikey.
"""


class Legiscan_API:

    def __init__(self):
        """Constructor for Legiscan_API. 
           Checks if a Legiscan_API apikey exists."""
        try:
            self.apiKey = os.environ['LEGISCAN_API_KEY']
            if not self.apiKey:
                raise Exception()
            self.url = "https://api.legiscan.com/?key=" + self.apiKey + "&op="
        except Exception:
            logging.error("Error: no valid LEGISCAN_API_KEY detected.")
        return None

    def getBill(self, billID):
        """Return the document id (docID) for a given bill id."""
        docID = None
        LastDate = "0000-00-00"
        try:
            billdetails = requests.get(self.url + "getBill&id=" + billID)
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
        except Exception as e:
            logging.error("Error: error getting document number. " + str(e))
        return docID, LastDate

    def getBillText(self, docID):
        """Return base64 encoded bill text based on given document id."""
        try:
            billText = requests.get(self.url + "getBillText&id=" + docID)
            return billText.json()['text']
        except Exception as e:
            logging.error("Error: error getting bill text. " + str(e))
        return None

    def getAllBills(self, state, json_filename, limit=10):
        """Create a json file of all bill for a given state. Each object
            represents a bill and contains bill_id, number, title,
            description, mime, and bill_text."""

        jsonForm = "{}.json"
        json_handle = jsonForm.format(state)
        try:
            problem_happened = False
            state_url = self.url + "getMasterList&state=" + state
            stateBills = requests.get(state_url)
            response = stateBills.json()

            # Legiscan imposes a limit of 30,000 requests per month
            # If the limit is exceeded, print message response here.
            if 'status' in response:
                if response['status'] == 'ERROR':
                    print(response['alert'])
                    problem_happened = True

            bills = {}
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

            elif fob.handle_exists(fob, json_handle):
                json_str = fob.download_text(json_handle)
                bills = json.loads(json_str)

            else:
                print('Unable to get latest info from Legiscan.com, ')
                print('and {} does not already exist.'.format(json_handle))
                return None

            dot = ShowProgress()
            details, num = 0, 0
            num_bills = len(bills)
            for i in bills:
                if "doc_id" in bills[i]:
                    details += 1
            
            # We have three scanning modes:
            # Mode 1: Fetch every bill fresh, high limit or unlimited,
            #         getting the latest doc_id and doc_date for all bills.
            if limit == 0 or limit >= num_bills:
                for i in bills:
                    self.fetch_bill(bills, i)
                    dot.show()

            # Mode 2: if limit is placed, only fetch bills that are
            #         missing details like doc_id and doc_date.
            elif limit > 0 and details < num_bills:
                for i in bills:
                    if "doc_id" not in bills[i]:
                        self.fetch_bill(bills, i)
                        num += 1
                        dot.show()
                        if num >= limit:
                            break

            # Mode 3: if limit is placed, and all bills have previously
            #         fetched details, randomly refresh scattered bills.
            elif limit < num_bills:
                for j in range(limit):
                    i = randint(0, num_bills)
                    self.fetch_bill(bills, i)
                    dot.show()
            dot.end()

            textdata = json.dumps(bills)
            fob.upload_textdata(textdata, json_handle)

            print("File {} uploaded".format(json_handle))
        except Exception as e:
            logging.error("Error: error getting state bills. " + str(e))

        return None

    def fetch_bill(bills, index):
        billID = str(bills[i]["bill_id"])
        docID, LastDate = self.getBill(billID)
        if docID:
            bills[i]["doc_id"] = docID
            bills[i]["doc_date"] = LastDate
        return None     


if __name__ == "__main__":
    if len(sys.argv) == 2:
        states = [sys.argv[1]]
    else:
        states = ['AZ', 'OH']

    leg = Legiscan_API()
    fob = FOB_Storage(settings.FOB_METHOD)
    for state in states:
        print('Processing: ', state)
        jsonForm = "{}.json"
        json_filename = jsonForm.format(state)
        leg.getAllBills(state, json_filename)
