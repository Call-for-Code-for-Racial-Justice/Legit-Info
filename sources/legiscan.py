#!/usr/bin/env python3
# scanjson.py -- Pull data from Legiscan API
# By Uchechukwu Uboh, IBM, 2020
#

import requests
import os
import logging
import json
import sys
from ShowProgress import ShowProgress

"""
    LegiScan class automates the retrival and curation of bill data for a
particular US state. Before running this class, your LegiScan apikey needs to
be an environmental variable with the key of "LEGISCAN_API_KEY". Visit
https://legiscan.com/legiscan to create your own LegiScan apikey.
"""


class LegiScan:
    def __init__(self):
        """Constructor for LegiScan. Checks if a LegiScan apikey exists."""
        try:
            self.apiKey = os.environ['LEGISCAN_API_KEY']
            if not self.apiKey:
                raise Exception()
            self.url = "https://api.legiscan.com/?key=" + self.apiKey + "&op="
        except Exception:
            logging.error("Error: no valid LegiScan api key detected.")
        return None

    def getBill(self, billID):
        """Return the document id (docID) for a given bill id."""
        docID = None
        try:
            billdetails = requests.get(self.url + "getBill&id=" + billID)
            billjson = billdetails.json()
            documents = None
            if billjson['status'] == 'OK':
                billinfo = billjson['bill']
                documents = billinfo['texts']
            Last = "0000-00-00"
            for doc in documents:
                docDate = doc['date']
                if docDate > Last:
                    docID = str(doc['doc_id'])
        except Exception as e:
            logging.error("Error: error getting document number. " + str(e))
        return docID

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
        dot = ShowProgress()
        try:
            stateBills = requests.get(
                self.url + "getMasterList&state=" + state)
            masterList = stateBills.json()["masterlist"]
            bills = {}

            for i in masterList:
                localDict = {}
                if "bill_id" in masterList[i]:
                    localDict["bill_id"] = masterList[i]["bill_id"]
                if "number" in masterList[i]:
                    localDict["number"] = masterList[i]['number']
                if "title" in masterList[i]:
                    localDict["title"] = masterList[i]['title']
                if "description" in masterList[i]:
                    localDict["description"] = masterList[i]['description']
                if len(localDict) > 0:
                    bills[len(bills)] = localDict
            for i in bills:
                billID = str(bills[i]["bill_id"])
                docID = self.getBill(billID)
                if docID:
                    response = self.getBillText(docID)
                    bills[i]["bill_text"] = response['doc']
                    bills[i]["mime"] = response['mime']
                    num += 1
                    dot.show()
            with open(state + ".json", 'w') as outfile:
                json.dump(bills, outfile)
        except Exception as e:
            logging.error("Error: error getting state bills. " + str(e))
        dot.end()
        return self


if __name__ == "__main__":
    if len(sys.argv) == 2:
        states = [sys.argv[1]]
    else:
        states = ['AZ', 'OH']

    leg = LegiScan()
    for state in states:
        leg.getAllBills(state)
