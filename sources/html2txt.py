#!/usr/bin/python3
# html2txt.py -- Convert Legiscan.com HTML to TXT file
# By Tony Pearson, IBM, 2020
#
import sys
from bs4 import BeautifulSoup
PARSER = "lxml"


class Oneline():
    """
    Class to maintain one long line

    """

    def __init__(self, dotchar="."):
        """ Set characters to use for showing progress"""
        self.oneline = ''
        return None

    def add_text(self, line):
        newline = line.replace("'", " ").replace('"', ' ').splitlines()
        newline2 = ' '.join(newline)
        self.oneline += newline2
        return self

    def write_file(self, outfile):
        print(self.oneline, file=outfile)
        return self


def parse_html(htmlname):
    page = open(htmlname, "rb").read().decode('utf-8', 'ignore')
    soup = BeautifulSoup(page, PARSER)
    title = soup.find('title')
    output_line.add_text('Legislation: {}'.format(title.string))

    sections = soup.findAll("span", {"class": "SECHEAD"})
    for section in sections:
        rawtext = section.string
        if rawtext:
            lines = rawtext.splitlines()
            header = " ".join(lines)
            output_line.add_text('Header: {}'.format(header))

    paragraphs = soup.findAll("p", {"class": "P06-00"})
    for paragraph in paragraphs:
        pg = paragraph.string
        if pg:
            output_line.add_text(pg)

    return None


def get_parms(argv):
    display_help = False
    if len(sys.argv) == 2:
        htmlname = sys.argv[1]
        if htmlname == '--help' or htmlname == '-h':
            display_help = True
        if not htmlname.endswith('.html'):
            display_help = True
    else:
        display_help = True

    if display_help:
        print('Syntax:')
        print(sys.argv[0], 'input_file.html')
        print(' ')

    return display_help, htmlname


if __name__ == "__main__":
    # Check proper input syntax
    display_help, htmlname = get_parms(sys.argv)

    output_line = Oneline()
    if not display_help:
        outname = htmlname.replace('.html', '.txt')
        with open(outname, "w") as outfile:
            parse_html(htmlname)
            output_line.write_file(outfile)

    print("File {} created".format(outname))
