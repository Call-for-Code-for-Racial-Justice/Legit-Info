#!/usr/bin/env python3
# LegiscanAPI.py -- Pull data from Legiscan.com API
# By Uchechukwu Uboh and Tony Pearson, IBM, 2020
#
# LegiscanAPI class automates the retrival and curation of bill data for a
# particular US state. Before running this class, your Legiscan.com apikey
# needs to be an environmental variable with the key of "LEGISCAN_API_KEY".
# Visit https://legiscan.com/legiscan to create your own Legiscan.com apikey.
#
# Debug with:  # import pdb; pdb.set_trace()

import logging
import json
import os
from random import randint
import requests
from cfc_app.DataBundle import DataBundle


class LegiscanError(Exception):
    pass


class APIkeyError(LegiscanError):
    pass


class LegiscanAPI:

    def __init__(self):
        """Constructor for LegiscanAPI.
           Checks if a LegiscanAPI apikey exists."""
        self.apiKey = os.getenv('LEGISCAN_API_KEY', None)
        if not self.apiKey:
            raise APIkeyError

        self.badKey = os.getenv('LEGISCAN_BAD_KEY', None)
        self.url = "https://api.legiscan.com/"
        self.api_ok = True    # assume safe to use API
        # self.fob = FOB_Storage(settings.FOB_METHOD)
        return None

    def getDatasetList(self, apikey='Good'):
        """ Get list of datasets for all 50 states """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        list_data = None
        dsl_bundle = DataBundle('getDataSetList')
        dsl_params = {'key': key, 'op': 'getDatasetList'}
        # import pdb; pdb.set_trace()
        success = self.invoke_api(dsl_bundle, dsl_params)
        if success:
            if 'datasetlist' in dsl_bundle.json_pkg:
                list_data = dsl_bundle.text
            else:
                dsl_bundle.ok = False
                dsl_bundle.status_code = 487

        if not dsl_bundle.ok:
            print('Failure', dsl_bundle)
            self.api_ok = False
            list_data = None
        return list_data

    def getDataset(self, session_id, access_key, apikey='Good'):
        """ Get datasets for individual legislative session """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        sesh_data = None
        sesh_bundle = DataBundle('getDataset')
        sesh_params = {'key': key, 'op': 'getDataset',
                       'id': session_id, 'access_key': access_key}

        success = self.invoke_api(sesh_bundle, sesh_params)
        if success:
            if 'dataset' in sesh_bundle.json_pkg:
                sesh_data = sesh_bundle.text
            else:
                sesh_bundle.ok = False
                sesh_bundle.status_code = 487

        if not sesh_bundle.ok:
            print('Failure', sesh_bundle)
            self.api_ok = False
            sesh_data = None
        return sesh_data

    def getMasterList(self, session_id, apikey='Good'):
        """ Get datasets for individual legislative session """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        mast_data = None
        mast_bundle = DataBundle('getDataset')
        mast_params = {'key': key, 'op': 'getMasterList', 'id': session_id}

        success = self.invoke_api(mast_bundle, mast_params)
        if success:
            if 'masterlist' in mast_bundle.json_pkg:
                mast_data = mast_bundle.text
            else:
                mast_bundle.ok = False
                mast_bundle.status_code = 487

        if not mast_bundle.ok:
            print('Failure', mast_bundle)
            self.api_ok = False
            mast_data = None
        return mast_data

    def invoke_api(self, bundle, params):
        """ Invoke the Legiscan API """
        EXCEEDED = "maximum query count"
        bundle.ok = False
        if self.api_ok:
            try:
                response = bundle.make_request(self.url, params)
                result = bundle.load_response(response)
                if result:
                    if bundle.extension == 'json':
                        if bundle.json_pkg['status'] == 'ERROR':
                            self.api_ok = False
                            bundle.ok = False
                            bundle.status_code = 406
                            pkg = bundle.json_pkg
                            if 'alert' in pkg:
                                bundle.name += ' *ERROR*'
                                bundle.text = ('ERROR: ' +
                                               pkg['alert']['message'])
                                if EXCEEDED in bundle.text:
                                    bundle.status_code = 429
                    else:
                        bundle.ok = False
                        bundle.status_code = 415
            except Exception as e:
                print('Error {}'.format(e))
                self.api_ok = False
                bundle.ok = False
                bundle.status_code = 403
        else:
            bundle.status_code = 405
        return bundle.ok

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

            # Mode 2: if limit is placed, only fetch bills that are
            #         missing detail like doc_id and doc_date.
            elif limit > 0 and detail < num_bills:
                for index in bills:
                    if "doc_id" not in bills[index]:
                        self.fetch_bill(bills, index)
                        num += 1
                        if num >= limit:
                            break

            # Mode 3: if limit is placed, and all bills have previously
            #         fetched detail, randomly refresh scattered bills.
            elif limit < num_bills:
                for j in range(limit):
                    index = randint(0, num_bills)
                    self.fetch_bill(bills, index)

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


if __name__ == "__main__":

    leg = LegiscanAPI()

    save_api_ok = leg.api_ok
    leg.api_ok = False
    params = {}
    bundle01 = DataBundle('Test1')
    print('Test with API_OK, no params, API_OK', leg.api_ok)
    r01 = leg.invoke_api(bundle01, params)
    print('Result:', r01, bundle01)

    leg.api_ok = True
    bundle02 = DataBundle('Test2')
    print('Test with no params, API_OK=', leg.api_ok)
    r02 = leg.invoke_api(bundle02, params)
    print('Result:', r02, bundle02)

    bundle02b = DataBundle('Test2b')
    dsl_params = {'key': leg.badKey}
    r02b = leg.invoke_api(bundle02b, params)
    print('Result:', r02b, bundle02b)

    bundle02c = DataBundle('Test2c')
    dsl_params = {'op': 'getDatasetList'}
    r02c = leg.invoke_api(bundle02c, params)
    print('Result:', r02c, bundle02c)

    # import pdb; pdb.set_trace()
    print('Test getDatasetList with bad API key')
    r03 = leg.getDatasetList(apikey='Bad')
    print('Result: ', r03, 'API_OK=', leg.api_ok)
    leg.api_ok = True

    print('Test getDatasetList with good API key')
    r04 = leg.getDatasetList(apikey='Good')
    print('Result:', len(r04))

    r04_pkg = json.loads(r04)
    print(r04_pkg['status'], len(r04_pkg['datasetlist']))
    dsl = r04_pkg['datasetlist']

    first_sesh = dsl[0]
    session_id = first_sesh['session_id']
    access_key = first_sesh['access_key']

    print('Test getDataset with bad API key')
    r05 = leg.getDataset(session_id, access_key, apikey='Bad')
    print('Result: ', r05)
    leg.api_ok = True

    print('Test getDataset with invalid session id')
    r06 = leg.getDataset(9999, access_key, apikey='Good')
    print('Result: ', r06)

    leg.api_ok = True
    print('Test getDataset with invalid access key')
    r07 = leg.getDataset(session_id, '', apikey='Good')
    print('Result: ', r07)

    leg.api_ok = True
    print('Test getDataset')
    r08 = leg.getDataset(session_id, access_key, apikey='Good')
    print('Result: ', len(r08))

    print('Test getMasterList')
    r09 = leg.getMasterList(session_id, apikey='Good')
    print('Result: ', len(r09))
