#!/usr/bin/python3
# html2txt.py -- Convert Legiscan.com HTML to TXT file
# By Tony Pearson, IBM, 2020
#
import sys
from bs4 import BeautifulSoup
PARSER = "lxml"


def parse_html(htmlname):
    page = open(htmlname, "rb").read().decode('utf-8', 'ignore')
    soup = BeautifulSoup(page, PARSER)
    title = soup.find('title')
    print('Legislation: {}'.format(title.string), file=outfile)

    sections = soup.findAll("span", {"class": "SECHEAD"})
    for section in sections:
        rawtext = section.string
        if rawtext:
            lines = rawtext.splitlines()
            header = " ".join(lines)
            print('Header: {}'.format(header), file=outfile)

    paragraphs = soup.findAll("p", {"class": "P06-00"})
    for paragraph in paragraphs:
        pg = paragraph.string
        if pg:
            print(pg, file=outfile)

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
    if not display_help:
        outname = htmlname.replace('.html', '.txt')
        with open(outname, "w") as outfile:
            parse_html(htmlname)

    print("File {} created".format(outname))
