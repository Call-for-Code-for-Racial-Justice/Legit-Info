import requests
import os
import logging
import json

"""
    LegiScan class automates the retrival and curation of bill data for a particular US state. Before running this class, your LegiScan apikey needs to be an environmental variable with the key of "LEGISCAN_API_KEY". Visit https://legiscan.com/legiscan to create your own LegiScan apikey.
"""

class LegiScan:
    def __init__ (self):
        """Constructor for LegiScan. Checks if a LegiScan apikey exists."""
        try:
            self.apiKey = os.environ['LEGISCAN_API_KEY']
            if not self.apiKey:
                raise Exception()
            self.url = "https://api.legiscan.com/?key=" + self.apiKey + "&op="
        except Exception:
            logging.error("Error: no valid LegiScan api key detected.")

    def getBillText(self, billID):
        """Return base64 encoded bill text based on given bill id."""
        try:
            billText = requests.get(self.url + "getBillText&id=" + billID)
            return billText.json()['text']['doc']
        except Exception as e:
            logging.error("Error: error getting bill text. " + str(e))

    def getAllBills(self, state):
        """Create a json file of all bill for a given state. Each object represents a bill and contains bill_id, number, title, description and bill_text."""
        try:
            stateBills = requests.get(self.url + "getMasterList&state=" + state)
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
                bills[i]["bill_text"] = self.getBillText(str(bills[i]["bill_id"]))
            with open("./" + state + ".json", 'w') as outfile:
                json.dump(bills, outfile)
        except Exception as e:
            logging.error("Error: error getting state bills. " + str(e))