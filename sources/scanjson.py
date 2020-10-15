#!/usr/bin/env python3
# scanjson.py -- Scan JSON from Legiscan API
# By Tony Pearson, IBM, 2020
#
import base64
import codecs
import json
import re
import sys
from bs4 import BeautifulSoup
from ShowProgress import ShowProgress

PARSER = "lxml"

charForm = "{} for {} on {} from position {} to {}. Using '?' in-place of it!"


class Oneline():
    """ Class to maintain one long line  """

    def __init__(self, dotchar="."):
        """ Set characters to use for showing progress"""
        self.oneline = ''
        return None

    def add_text(self, line):
        newline = line.replace("'", " ").replace('"', ' ').splitlines()
        newline2 = ' '.join(newline)
        self.oneline += newline2 + ' '
        return self

    def write_file(self, outfile):
        print(self.oneline, end='', file=outfile)
        return self

    def write_name(self, outname):
        with open(outname, "w") as outfile:
            self.write_file(outfile)
        return self


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


def parse_html(in_line, out_line):
    soup = BeautifulSoup(in_line, PARSER)
    title = soup.find('title')
    if title:
        out_line.add_text(title.string)

    sections = soup.findAll("span", {"class": "SECHEAD"})
    for section in sections:
        rawtext = section.string
        if rawtext:
            lines = rawtext.splitlines()
            header = " ".join(lines)
            out_line.add_text(header)

    paragraphs = soup.findAll("p")
    for paragraph in paragraphs:
        pg = paragraph.string
        if pg:
            out_line.add_text(pg)

    return None


def process_html(billname, title, summary, billtext, textname):
    with open(billname, "w") as billfile:
        print(billtext, file=billfile)
    html_line = Oneline()
    html_line.add_text(billname)
    html_line.add_text(title)
    html_line.add_text(summary)
    parse_html(billtext, html_line)
    html_line.write_name(textname)
    return None


def remove_section_numbers(line):
    newline = re.sub(r'and [-0-9]+[.][0-9]+\b\s*', '', line)
    newline = re.sub(r'\([-0-9]+[.][0-9]+\)[,]?\s*', '', newline)
    newline = re.sub(r'\b[-0-9]+[.][0-9]+\b[,]?\s*', '', newline)
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


def determine_extension(mime_type):
    extension = 'unk'
    if mime_type == 'text/html':
        extension = 'html'
    elif mime_type == 'application/pdf':
        extension = 'pdf'
    elif mime_type == 'application/doc':
        extension = 'doc'

    return extension


def custom_character_handler(exception):
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
    dot = ShowProgress()
    if not display_help:
        with open(jsonname, "r") as jsonfile:
            data = json.load(jsonfile)
            num = 0

            for entry in data:
                num += 1
                dot.show()
                bill = data[entry]
                key = "{}-{}".format(state, bill['number'])
                print('KEY: ', key)

                title = remove_section_numbers(bill['title'])
                summary = remove_section_numbers(bill['description'])

                if len(title) > 200:
                    revised = shrink_line(title, 200)

                if len(summary) > 1000:
                    revised = shrink_line(summary, 1000)

                if 'mime' not in bill:
                    continue
                mime_type = bill['mime']
                mimedata = bill['bill_text'].encode('latin-1')
                msg_bytes = base64.b64decode(mimedata)
                try:
                    billtext = msg_bytes.decode('latin-1')
                except TypeError:
                    print('Error')

                extension = determine_extension(mime_type)
                print(key, mime_type, extension)
                billname = '{}.{}'.format(key, extension)
                textname = '{}.{}'.format(key, 'txt')

                if extension == 'html':
                    process_html(billname, title, summary, billtext, textname)

                if num >= 50:
                    break
    dot.end()
    print('Done.')
