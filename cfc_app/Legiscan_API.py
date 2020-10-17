#!/usr/bin/env python3
# Legiscan_API.py -- Pull data from Legiscan.com API
# By Uchechukwu Uboh, IBM, 2020
# Updated by Tony Pearson, IBM -- 2020-10-15
#

import requests
import os
import logging
import json
import sys
from cfc_app.ShowProgress import ShowProgress
from django.conf import settings

"""
    Legiscan_API class automates the retrival and curation of bill data for a
particular US state. Before running this class, your Legiscan.com apikey needs
to be an environmental variable with the key of "LEGISCAN_API_KEY". Visit
https://legiscan.com/legiscan to create your own Legiscan.com apikey.
"""

class Legiscan_API:
    def __init__(self):
        """Constructor for Legiscan_API. Checks if a Legiscan_API apikey exists."""
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

    def getAllBills(self, state):
        """Create a json file of all bill for a given state. Each object
            represents a bill and contains bill_id, number, title,
            description, mime, and bill_text."""
        num = 0
        fullname = os.path.join(settings.SOURCE_ROOT, state+".json")
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

            if 'masterlist' not in response:
                problem_happened = True

            if problem_happened:
                if os.path.exists(fullname):
                    print('Will use previous fetch: ', fullname)
                return

            masterList = response["masterlist"]
            bills = {}

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
            dot = ShowProgress()       
            for i in bills:
                billID = str(bills[i]["bill_id"])
                docID, LastDate = self.getBill(billID)
                if docID:
                    bills[i]["doc_id"] = docID
                    bills[i]["doc_date"] = LastDate
                    num += 1
                    dot.show()
            
            with open(fullname, 'w') as outfile:
                json.dump(bills, outfile)

            dot.end()
            print("File {} written".format(fullname))
        except Exception as e:
            logging.error("Error: error getting state bills. " + str(e))
        
        return self


if __name__ == "__main__":
    if len(sys.argv) == 2:
        states = [sys.argv[1]]
    else:
        states = ['AZ', 'OH']

    leg = Legiscan_API()
    for state in states:
        print('Processing: ', state)   
        leg.getAllBills(state)
