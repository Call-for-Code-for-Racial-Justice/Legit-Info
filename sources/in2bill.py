#!/usr/bin/env python3
# in2bill.py -- Takes output of pdfminer.six PDF2TXT.PY and cleans output
# By Tony Pearson, IBM, 2020
#
import sys


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
        self.oneline += newline2 + ' '
        return self

    def write_file(self, outfile):
        print(self.oneline, end='', file=outfile)
        return self


def parse_input(input_string):
    lines = input_string.splitlines()
    for line in lines:
        newline = line.replace('B I L L', 'BILL')
        newline = newline.strip()
        # Remove lines that only contain blanks or line numbers only
        if newline != '' and not newline.isdigit():
            output_line.add_text(newline)
    return None


def read_file(inputname):
    if inputname == '-':
        input_str = sys.stdin.read()
    else:
        with open(inputname, "r") as infile:
            input_str = infile.read()
    return input_str


def get_parms(argv):
    display_help = False
    filename = ''
    if len(sys.argv) == 3:
        inputname = sys.argv[1]
        outputname = sys.argv[2]
        if inputname == '--help' or inputname == '-h':
            display_help = True
        if not outputname.endswith('.txt'):
            display_help = True
    else:
        display_help = True

    if display_help:
        print('Syntax:')
        print('./PDF2TEXT.py input.pdf | ',sys.argv[0], '- output.txt')
        print(sys.argv[0], 'input.file', 'output.txt')
        print(' ')

    return display_help, inputname, outputname


if __name__ == "__main__":
    # Check proper input syntax
    display_help, inputname, outname = get_parms(sys.argv)

    output_line = Oneline()
    
    if not display_help:
        with open(outname, "w") as outfile:
            input_str = read_file(inputname)
            parse_input(input_str)
            output_line.write_file(outfile)

    print("File {} created".format(outname))
