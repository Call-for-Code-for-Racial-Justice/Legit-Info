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


import sys
import pdfminer.high_level
import pdfminer.layout

OUTPUT_TYPES = ((".htm", "html"),
                (".html", "html"),
                (".xml", "xml"),
                (".tag", "tag"))


class PDFtoTEXT():
    """
    Class to handle PDF files
    """

    def __init__(self, input_name, output_name):
        """ Set characters to use for showing progress"""
        self.input_name = input_name
        self.output_name = output_name
        outfp = self.extract_text(files=[input_name], outfile=output_name)
        outfp.close()
        return None

    def extract_text(self, files=[], outfile='-',
                     no_laparams=False, all_texts=None, detect_vertical=None,
                     word_margin=None, char_margin=None, line_margin=None,
                     boxes_flow=None, output_type='text', codec='utf-8',
                     strip_control=False, maxpages=0, page_numbers=None,
                     password="", scale=1.0, rotation=0, layoutmode='normal',
                     output_dir=None, debug=False, disable_caching=False,
                     **kwargs):
        if not files:
            raise ValueError("Must provide files to work upon!")

        if not no_laparams:
            laparams = pdfminer.layout.LAParams()
            for param in ("all_texts", "detect_vertical", "word_margin",
                          "char_margin", "line_margin", "boxes_flow"):
                paramv = locals().get(param, None)
                if paramv is not None:
                    setattr(laparams, param, paramv)
        else:
            laparams = None

        if output_type == "text" and outfile != "-":
            for override, alttype in OUTPUT_TYPES:
                if outfile.endswith(override):
                    output_type = alttype

        if outfile == "-":
            outfp = sys.stdout
            if outfp.encoding is not None:
                codec = 'utf-8'
        else:
            outfp = open(outfile, "wb")

        for fname in files:
            with open(fname, "rb") as fp:
                pdfminer.high_level.extract_text_to_fp(fp, **locals())
        return outfp
