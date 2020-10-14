#!/usr/bin/env python3
# scantext.py -- Scan JSON from Legiscan API
# By Tony Pearson, IBM, 2020
#
import base64
import json
import sys


def get_parms(argv):
    display_help = False
    filename = ''
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if filename == '--help' or filename == '-h':
            display_help = True
        if not filename.endswith('.json'):
            display_help = True
    else:
        display_help = True

    if display_help:
        print('Syntax:')
        print(sys.argv[0], 'input_file.json')
        print(' ')

    return display_help, filename


if __name__ == "__main__":
    # Check proper input syntax
    display_help, jsonname = get_parms(sys.argv)

    if not display_help:
        with open(jsonname, "r") as jsonfile:
            data = json.load(jsonfile)
            print('Status = ', data['status'])
            masterlist = data['text']
            mimetype = masterlist['mime']
            mimedata = masterlist['doc'].encode('utf-8')
            msg_bytes = base64.b64decode(mimedata)
            billtext = msg_bytes.decode('utf-8')
            print(billtext)

print('Done.')
