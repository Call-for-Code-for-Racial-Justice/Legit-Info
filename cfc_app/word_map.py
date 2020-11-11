#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Load word mapping relevant terms to impact areas.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging
import os
import re

# Django and other third-party imports
from django.conf import settings

# Application imports

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class WordMapError(RuntimeError):
    """ Customize error for this class """
    pass


class WordMap():
    """ Class to handle wordmap for analyze_text  """

    def __init__(self, rlimit):
        """ Initialize wordmap """
        self.wordmap = None
        self.primary = None
        self.secondary = None
        self.tertiary = None
        self.secondary_impacts = None
        self.rlimit = rlimit
        self.regex = re.compile(r'["](.*)["]\s*,\s*["](.*)["]')
        self.impact_list = None
        self.categories = None
        return None

    def load_csv(self, impact_list):
        """ load wordmap """

        self.impact_list = impact_list
        self.wordmap, self.categories = {}, []
        mapname = os.path.join(settings.SOURCE_ROOT, 'wordmap.csv')
        logger.debug(f"171:Mapname: {mapname}")

        with open(mapname, 'r') as mapfile:
            maplines = mapfile.readlines()

        logger.debug(f"165:maplines {len(maplines)}")
        for line in maplines:
            mop = self.regex.search(line)
            if mop:
                term = mop.group(1).strip()
                impact_category = mop.group(2).strip()
                if term == 'term' or impact_category == 'impact':
                    continue
                if impact_category.upper() in ['REMOVE']:
                    continue
                if impact_category.upper() in ['NONE']:
                    impact_category = 'None'
                self.wordmap[term] = impact_category
                if impact_category not in self.categories:
                    self.categories.append(impact_category)
            else:
                logger.error(f"181:Regex Error {line}")

        self.review_categories()

        return None

    def review_categories(self):
        """ Review categories found """

        secondary_list = []
        topic_list = []
        for impact in self.categories:
            marker = ' '
            if impact in self.impact_list:
                marker = '*'
            elif impact != 'None':
                secondary_list.append(impact)
            topic_list.append(marker+impact)

        topic_msg = "Impacts marked with * match cfc_app_impact table"
        logger.debug(f"200: {topic_msg}: {topic_list}")

        self.secondary_impacts = secondary_list

        primary, secondary, tertiary = [], [], []
        for term in self.wordmap:
            if self.wordmap[term] in self.impact_list:
                primary.append([term, self.wordmap[term]])
            elif self.wordmap[term] in secondary_list:
                secondary.append([term, self.wordmap[term]])
            else:
                tertiary.append([term, self.wordmap[term]])

        logger.debug(f"215:Primary {len(primary)}")
        logger.debug(f"216:Secondary {len(secondary)}")
        logger.debug(f"217:Tertiary {len(tertiary)}")

        self.primary = primary
        self.secondary = secondary
        self.tertiary = tertiary
        return None

    def relevance(self, extracted_text):
        """ return top impact areas from extracted text """

        concept = self.scan_extract(extracted_text, self.primary)
        if len(concept) < self.rlimit:
            concept += self.scan_extract(extracted_text, self.secondary)

        # If we have already found primary/secondary, do not bother with NONE
        if len(concept) == 0:
            concept += self.scan_extract(extracted_text, self.tertiary)

        return concept

    def scan_extract(self, extracted_text, category_list):
        """ Scan extracted text for relevant keywords """

        relterms, concept = {}, []
        for rel in category_list:
            term = rel[0]
            rec = re.compile(r"\b"+term+r"\b", re.IGNORECASE)
            matches = rec.findall(extracted_text)
            if matches:
                relterms[term] = len(matches)

        num = 0
        # import pdb; pdb.set_trace()
        for term, count in sorted(relterms.items(), key=lambda item: item[1],
                                  reverse=True):
            logger.debug(f"328:WORDMAP {term} {count} {self.wordmap[term]}")

            concept.append({'text': term, 'Reason': self.wordmap[term]})
            num += 1
            if num >= self.rlimit:
                break

        return concept

# end of module
