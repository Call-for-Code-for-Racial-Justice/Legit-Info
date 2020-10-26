#!/usr/bin/env python3
# LegiscanAPI.py -- Pull data from Legiscan.com API
# By Uchechukwu Uboh and Tony Pearson, IBM, 2020
#
# LegiscanAPI class automates the retrival and curation of bill data for a
# particular US state. Before running this class, your Legiscan.com apikey
# needs to be an environmental variable with the key of "LEGISCAN_API_KEY".
# Visit https://legiscan.com/legiscan to create your own Legiscan.com apikey.
#
# See /docs/Legiscan/ for API manual and Entity relationship diagram (ERD)
#
# Debug with:  # import pdb; pdb.set_trace()

import json
import os
from cfc_app.DataBundle import DataBundle

LEGISCAN_ID = {
    1: {"code": "AL", "name": "Alabama", "capital": "Montgomery"},
    2: {"code": "AK", "name": "Alaska", "capital": "Juneau"},
    3: {"code": "AZ", "name": "Arizona", "capital": "Phoenix"},
    4: {"code": "AR", "name": "Arkansas", "capital": "Little Rock"},
    5: {"code": "CA", "name": "California", "capital": "Sacramento"},
    6: {"code": "CO", "name": "Colorado", "capital": "Denver"},
    7: {"code": "CT", "name": "Connecticut", "capital": "Hartford"},
    8: {"code": "DE", "name": "Delaware", "capital": "Dover"},
    9: {"code": "FL", "name": "Florida", "capital": "Tallahassee"},
    10: {"code": "GA", "name": "Georgia", "capital": "Atlanta"},
    11: {"code": "HI", "name": "Hawaii", "capital": "Honolulu"},
    12: {"code": "ID", "name": "Idaho", "capital": "Boise"},
    13: {"code": "IL", "name": "Illinois", "capital": "Springfield"},
    14: {"code": "IN", "name": "Indiana", "capital": "Indianapolis"},
    15: {"code": "IA", "name": "Iowa", "capital": "Des Moines"},
    16: {"code": "KS", "name": "Kansas", "capital": "Topeka"},
    17: {"code": "KY", "name": "Kentucky", "capital": "Frankfort"},
    18: {"code": "LA", "name": "Louisiana", "capital": "Baton Rouge"},
    19: {"code": "ME", "name": "Maine", "capital": "Augusta"},
    20: {"code": "MD", "name": "Maryland", "capital": "Annapolis"},
    21: {"code": "MA", "name": "Massachusetts", "capital": "Boston"},
    22: {"code": "MI", "name": "Michigan", "capital": "Lansing"},
    23: {"code": "MN", "name": "Minnesota", "capital": "Saint Paul"},
    24: {"code": "MS", "name": "Mississippi", "capital": "Jackson"},
    25: {"code": "MO", "name": "Missouri", "capital": "Jefferson City"},
    26: {"code": "MT", "name": "Montana", "capital": "Helena"},
    27: {"code": "NE", "name": "Nebraska", "capital": "Lincoln"},
    28: {"code": "NV", "name": "Nevada", "capital": "Carson City"},
    29: {"code": "NH", "name": "New Hampshire", "capital": "Concord"},
    30: {"code": "NJ", "name": "New Jersey", "capital": "Trenton"},
    31: {"code": "NM", "name": "New Mexico", "capital": "Santa Fe"},
    32: {"code": "NY", "name": "New York", "capital": "Albany"},
    33: {"code": "NC", "name": "North Carolina", "capital": "Raleigh"},
    34: {"code": "ND", "name": "North Dakota", "capital": "Bismarck"},
    35: {"code": "OH", "name": "Ohio", "capital": "Columbus"},
    36: {"code": "OK", "name": "Oklahoma", "capital": "Oklahoma City"},
    37: {"code": "OR", "name": "Oregon", "capital": "Salem"},
    38: {"code": "PA", "name": "Pennsylvania", "capital": "Harrisburg"},
    39: {"code": "RI", "name": "Rhode Island", "capital": "Providence"},
    40: {"code": "SC", "name": "South Carolina", "capital": "Columbia"},
    41: {"code": "SD", "name": "South Dakota", "capital": "Pierre"},
    42: {"code": "TN", "name": "Tennessee", "capital": "Nashville"},
    43: {"code": "TX", "name": "Texas", "capital": "Austin"},
    44: {"code": "UT", "name": "Utah", "capital": "Salt Lake City"},
    45: {"code": "VT", "name": "Vermont", "capital": "Montpelier"},
    46: {"code": "VA", "name": "Virginia", "capital": "Richmond"},
    47: {"code": "WA", "name": "Washington", "capital": "Olympia"},
    48: {"code": "WV", "name": "West Virginia", "capital": "Charleston"},
    49: {"code": "WI", "name": "Wisconsin", "capital": "Madison"},
    50: {"code": "WY", "name": "Wyoming", "capital": "Cheyenne"},
    51: {"code": "DC", "name": "Washington D.C.", "capital": "Washington, DC"},
    52: {"code": "US", "name": "US Congress", "capital": "Washington, DC"},
}


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
                                bundle.text = ('*ERROR* ' +
                                               pkg['alert']['message'])
                                bundle.text += " " + self.url
                                bundle.text += " " + json.dumps(params)
                                if EXCEEDED in bundle.text:
                                    bundle.status_code = 429
                                raise LegiscanError(
                                    bundle.name+" "+bundle.text)
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

    def getBillText(self, document_id, apikey='Good'):
        """ Get specific document identified in bill """
        key = self.badKey
        if apikey == 'Good':
            key = self.apiKey

        bill_data = None
        bill_bundle = DataBundle('getDataset')
        bill_params = {'key': key, 'op': 'getDataset', 'id': document_id}

        success = self.invoke_api(bill_bundle, bill_params)
        if success:
            if 'text' in bill_bundle.json_pkg:
                bill_data = bill_bundle.text
            else:
                bill_bundle.ok = False
                bill_bundle.status_code = 487

        if not bill_bundle.ok:
            print('Failure', bill_bundle)
            self.api_ok = False
            bill_data = None
        return bill_data


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
