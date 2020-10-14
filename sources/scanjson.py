#!/usr/bin/env python3
# scanjson.py -- Scan JSON from Legiscan API
# By Tony Pearson, IBM, 2020
#
import base64
import codecs
import json
import re
import sys

charForm = "{} for {} on {} from position {} to {}. Using '?' in-place of it!"


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


def remove_section_numbers(line):
    newline = re.sub(r'and [0-9]+[.][0-9]+\b\s*', '', line)
    newline = re.sub(r'\([0-9]+[.][0-9]+\)[,]?\s*', '', newline)  
    newline = re.sub(r'\b[0-9]+[.][0-9]+\b[,]?\s*', '', newline)
    newline = re.sub(r'section[s]? and section[s]?\s*', 'sections', newline)
    newline = re.sub(r'section[s]?\s*;\s*', '; ', newline)
    newline = re.sub(r'amend; to amend,\s*', 'amend ', newline)
    newline = newline.replace("'", " ").replace('"', ' ')
    newline = newline.replace(r'\x91', '')
    return newline


def shrink_line(line, limit):
    newline = re.sub(r'^\W*\w*\W*', '', line[-limit:])
    newline = re.sub(r'^and ', '', newline)
    newline = newline[0].upper() + newline[1:]
    return newline


def determine_mime_type(line):
    mime_type = 'UNK'
    if line[:4] == '%PDF':
        mime_type = 'PDF'
    elif ('<!--' in line or
            '<pre>' in line or
            '<style>' in line or
            '<title>' in line or
            '<html>' in line):
        mime_type = 'HTML'
    return mime_type


def custom_character_handler(exception):
    errors_found = False
    # print(charForm.format(exception.reason,
    #        exception.object[exception.start:exception.end],
    #        exception.encoding,
    #        exception.start,
    #        exception.end ))
    return ("?", exception.end)


if __name__ == "__main__":
    # Check proper input syntax
    codecs.register_error("custom_character_handler", custom_character_handler)

    display_help, jsonname = get_parms(sys.argv)
    state = jsonname[:2].upper()

    if not display_help:
        with open(jsonname, "r") as jsonfile:
            data = json.load(jsonfile)
            num = 0
            for entry in data:
                num += 1
                bill = data[entry]
                key = "{}-{}".format(state, bill['number'])
                print('KEY: ', key)

                title = remove_section_numbers(bill['title'])
                summary = remove_section_numbers(bill['description'])

                if len(title)>200:
                    revised = shrink_line(title, 200)

                if len(summary)>1000:
                    revised = shrink_line(summary, 1000)


                mimedata = bill['bill_text'].encode('utf-8')
                msg_bytes = base64.b64decode(mimedata)
                errors_found = False
                try:
                    billtext = msg_bytes.decode('utf-8')
                except:
                    errors_found = True

                mime_type = determine_mime_type(billtext)
                print(key, mime_type, errors_found)
                billname = '{}.{}'.format(key, mime_type)
       #        if mime_type == 'HTML':
       #             with open(billname, "w") as billfile:
       #                 print(billtext, file=billfile)
       #         elif mime_type == 'PDF':
       #             with open(billname, "wb") as billfile:
       #                 billfile.write(msg_bytes)
       #         else:
       #             print(key, 'Mime type: ', mime_type)

                if num >=10:
                    break
print('Done.')
        

