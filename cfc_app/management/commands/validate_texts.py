#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scan TXT files, check for problems.
"""
# System imports
import re

# Django and other third-party imports
from django.core.management.base import BaseCommand
from django.conf import settings

# Application imports
from cfc_app.FOB_Storage import FOB_Storage
from cfc_app.ShowProgress import ShowProgress
from cfc_app.key_counter import KeyCounter

SecRegex = re.compile(r"^(Sec|SEC|Sub)[.]$")
DotRegex = re.compile(r"^[.]$")
NumRegex = re.compile(r"^[0-9][.]$")
UpRegex = re.compile(r"^[A-Z][.]$")
LowRegex = re.compile(r"^[a-z][.]$")
FullRegex = re.compile(r"^[A-Z]\w* .*[a-z][.]$")


class Command(BaseCommand):
    """ Customized command validate_texts """

    help = ("test1")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fob = FOB_Storage(settings.FOB_METHOD)
        self.filenames = KeyCounter('Filenames', toplist=False)
        self.slen = KeyCounter('Sentence Lengths', limit=25)
        self.numsen = KeyCounter('Number of Sentences', limit=25)
        self.stubs = KeyCounter("Bits and Pieces", limit=25)
        self.firsts = KeyCounter('First character', limit=10)
        self.lasts = KeyCounter('First character', limit=10)
        self.full = KeyCounter('Full Sentence Lengths', limit=25)
        self.fullsen = KeyCounter('Full Sentences', limit=25)
        return None

    def add_arguments(self, parser):
        return None

    def handle(self, *args, **options):
        """ Handle validate_texts command """

        items = self.fob.list_items(suffix=".txt", limit=0)
        print("Number of text files: ", len(items))
        dot = ShowProgress()
        count = 0
        for filename in items:
            self.process_file(filename)
            count += 1
            if (count % 100) == 0:
                dot.show()
        dot.end()
        self.show_results()
        return None

    def process_file(self, filename):
        """ process this text file """

        self.filenames.consider_key(filename)
        textdata = self.fob.download_text(filename)
        lines = textdata.splitlines()

        numfull = 0

        for line in lines:
            nlen = len(line)
            self.slen.consider_key(nlen)
            if nlen:
                firstchar = line[0]
                self.firsts.consider_key(firstchar)

            if nlen > 3:
                lastchar = line[-2]
                self.lasts.consider_key(lastchar)

            mop = FullRegex.search(line)
            if mop:
                self.full.consider_key(nlen)
                numfull += 1

        numsen = len(lines)
        self.numsen.consider_key(numsen)
        self.fullsen.consider_key(numfull)

        return None

    def show_results(self):
        """ Show results """

        self.filenames.key_results()
        self.slen.key_results()
        self.full.key_results()
        self.numsen.key_results()
        self.stubs.key_results()
        self.firsts.key_results()
        self.lasts.key_results()

        return None
# end
