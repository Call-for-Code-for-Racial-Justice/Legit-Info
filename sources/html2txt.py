#!/usr/bin/python3
# html2txt.py -- Convert Legiscan.com HTML to TXT file
# By Tony Pearson, IBM, 2020
#
import os
import re
import requests
import sys
from bs4 import BeautifulSoup
from urllib.request import urlopen
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

def parse(postname):
    """ Parse the post to extract all links """
    soup = BeautifulSoup(open(postname), PARSER)
    problems = []
    links = soup.select('a')
    for link in links:
        extlink = link.get('href')
        display_problems = False

        # Not all <a> tags have HREF links
        if extlink is None:
            display_problems = False
        # All links to IBM developerWorks need to be corrected
        elif extlink.startswith(DWORKS):
            display_problems = True
            code = 301
        # Eliminate boilerplate links, allow other links to be investigated
        elif allowlist(extlink):
            code = 404
            try:
                res = requests.get(extlink, timeout=5)
                code = res.status_code
            except Exception:
                code = 408
            if (code != requests.codes.ok):
                display_problems = True
        if display_problems:
            problems.append(str(code)+' '+extlink)

    # If problems with links found, print postname and list of problems
    if problems:
        print(postname, '-- problems found:', len(problems), file=out_file)
        for problem in problems:
            print('   ', problem, file=out_file)


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
        outname = htmlname.replace('.html','.txt')
        with open(outname, "w") as outfile:
            parse_html(htmlname)


    print("File {} created".format(outname))
