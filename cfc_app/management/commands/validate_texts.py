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

        sec_line = False
        dot_line = False
        num_line = False
        up_line = False
        low_line = False
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

            mo = FullRegex.search(line)
            if mo:
                self.full.consider_key(nlen)
                numfull += 1

            if nlen < 26:
                self.stubs.consider_key(line)
                mo = SecRegex.search(line)
                if mo:
                    sec_line = True
                mo = DotRegex.search(line)
                if mo:
                    dot_line = True
                mo = NumRegex.search(line)
                if mo:
                    num_line = True
                mo = UpRegex.search(line)
                if mo:
                    up_line = True
                mo = LowRegex.search(line)
                if mo:
                    low_line = True

        if (sec_line and dot_line
                and num_line and up_line and low_line):
            print("USE THIS: ", filename)
        numsen = len(lines)
        self.numsen.consider_key(numsen)
        self.fullsen.consider_key(numfull)

        return None

    def show_results(self):

        self.filenames.key_results()
        self.slen.key_results()
        self.full.key_results()
        self.numsen.key_results()
        self.stubs.key_results()
        self.firsts.key_results()
        self.lasts.key_results()

        return None
# end
