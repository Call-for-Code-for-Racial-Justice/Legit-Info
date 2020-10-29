"""A command line tool for extracting text and images from PDF and
output it to plain text, html, xml or tags."""
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
import sys

# Django and other third-party imports
import pdfminer.high_level
import pdfminer.layout
from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

class PDFtoTEXT():
    """
    Class to handle PDF files
    """

    def __init__(self, input_name):
        """ Set save input file name """
        self.input_name = input_name
        return None

    def convert_to_text(self):
        """ Set save input file name """
        output_string = StringIO()
        with open(self.input_name, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

        return output_string.getvalue()

    def extract_text2fp(pdf_file, password='', page_numbers=None, maxpages=0,
                 caching=True, codec='utf-8', laparams=None):
        """Parse and return the text contained in a PDF file.

        :param pdf_file: Either a file path or a file-like object for the PDF file
            to be worked on.
        :param password: For encrypted PDFs, the password to decrypt.
        :param page_numbers: List of zero-indexed page numbers to extract.
        :param maxpages: The maximum number of pages to parse
        :param caching: If resources should be cached
        :param codec: Text decoding codec
        :param laparams: An LAParams object from pdfminer.layout. If None, uses
            some default settings that often work well.
        :return: a string containing all of the text extracted.
        """
        if laparams is None:
            laparams = LAParams()

        with open_filename(pdf_file, "rb") as fp, StringIO() as output_string:
            rsrcmgr = PDFResourceManager(caching=caching)
            device = TextConverter(rsrcmgr, output_string, codec=codec,
                               laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
    
            for page in PDFPage.get_pages(
                    fp,
                    page_numbers,
                    maxpages=maxpages,
                    password=password,
                    caching=caching,
            ):
                interpreter.process_page(page)

        return output_string.getvalue()

if __name__ == "__main__":
    print('Thank you')
