#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from PDF file.

Modified slightly from PDFminer.six example by Tony Pearson, IBM, 2020
"""
# From https://github.com/pdfminer/pdfminer.six.git

# Copyright (c) 2004-2016  Yusuke Shinyama <yusuke at shinyama dot jp>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# System imports

# Django and other third-party imports
from io import BytesIO, StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


class PDFtoText():
    """
    Class to handle PDF files
    """

    def __init__(self, input_name, binary_input):
        """ Set save input file name """
        self.input_name = input_name
        self.binary_input = binary_input
        return None

    def convert_to_text(self):
        """ Set save input file name """
        input_io = BytesIO(self.binary_input)
        output_string = StringIO()
        with input_io as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

        return output_string.getvalue()


if __name__ == "__main__":
    TEST_PDF = "pdf_to_text_sample.pdf"
    TEST_OUT = "pdf_to_text_sample.txt"
    print('======================================= Converting: ', TEST_PDF)
    with open(TEST_PDF, "rb") as in_file:
        bindata = in_file.read()
        miner = PDFtoText(TEST_PDF, bindata)
        textdata = miner.convert_to_text()
        print(textdata[:300])
        with open(TEST_OUT, "w") as out_file:
            out_file.write(textdata)
        print("====================== Output text file created: ", TEST_OUT)

    print('========================= Thank you ===========================')
