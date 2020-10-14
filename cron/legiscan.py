import requests
import os
import logging
import json

class LegiScan:
    def __init__ (self):
        try:
            self.apiKey = os.environ['LEGISCAN_API_KEY']
            if not self.apiKey:
                raise Exception()
            self.url = "https://api.legiscan.com/?key=" + self.apiKey + "&op="
        except Exception:
            logging.error("Error: no valid LegiScan api key detected.")

    def getBillText(self, billID):
        try:
            billText = requests.get(self.url + "getBillText&id=" + billID)
            return billText.json()['text']['doc']
        except Exception as e:
            logging.error("Error: error getting bill text. " + str(e))

    def getAllBills(self, state):
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

leg1 = LegiScan()
leg1.getAllBills("az")