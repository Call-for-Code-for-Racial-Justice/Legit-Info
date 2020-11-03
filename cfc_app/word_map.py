#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Load word mapping relevant terms to impact areas.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging

# Django and other third-party imports
# Application imports
# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)


class WordMapError(RuntimeError):
    """ Customize error for this class """
    pass


class WordMap():
    """ Class to handle wordmap for analyze_text  """

    def __init__(self):
        """ Initialize wordmap """
        self.wordmap = None
        self.primary = None
        self.secondary = None
        self.tertiary = None
        self.secondary_impacts = None
        return None

    def load_wordmap(self, impact_list):
        """ load wordmap """

        wordmap, categories = {}, []
        mapname = os.path.join(settings.SOURCE_ROOT, 'wordmap.csv')
        logger.debug(f"171:Mapname: {mapname}")

        with open(mapname, 'r') as mapfile:
            maplines = mapfile.readlines()

        logger.debug(f"165:maplines {len(maplines)}")
        for line in maplines:
            mo = mapRegex.search(line)
            if mo:
                term = mo.group(1).strip()
                impact_category = mo.group(2).strip()
                if term == 'term' or impact_category == 'impact':
                    continue
                if impact_category.upper() in ['REMOVE']:
                    continue
                if impact_category.upper() in ['NONE']:
                    impact_category = 'None'
                wordmap[term] = impact_category
                if impact_category not in categories:
                    categories.append(impact_category)
            else:
                logger.error(f"181:Regex Error {line}")

        secondary_list = []
        topic_list = []
        for impact in categories:
            marker = ' '
            if impact in impact_list:
                marker = '*'
            elif impact != 'None':
                secondary_list.append(impact)
            topic_list.append(marker+impact)

        topic_msg = "Impacts marked with * match cfc_app_impact table"
        logger.debug(f"200: {topic_msg}: {topic_list}")

        self.wordmap = wordmap
        self.secondary_impacts = secondary_list

        primary, secondary, tertiary = [], [], []
        for term in wordmap:
            if wordmap[term] in impact_list:
                primary.append([term, wordmap[term]])
            elif wordmap[term] in secondary_list:
                secondary.append([term, wordmap[term]])
            else:
                tertiary.append([term, wordmap[term]])

        logger.debug(f"215:Primary {len(primary)}")
        logger.debug(f"216:Secondary {len(secondary)}")
        logger.debug(f"217:Tertiary {len(tertiary)}")

        self.primary = primary
        self.secondary = secondary
        self.tertiary = tertiary
        return None

    def Relevance(self, extracted_text):
        """ return top impact areas from extracted text using Wordmap """
        concept = []

        self.scan_extract(extracted_text, self.primary, concept)
        if len(concept) < RLIMIT:
            self.scan_extract(extracted_text, self.secondary, concept)
        if len(concept) < RLIMIT:
            self.scan_extract(extracted_text, self.tertiary, concept)

        return concept

    def scan_extract(self, extracted_text, category_list, concept):
        """ Scan extracted text for relevant keywords """

        relterms = {}
        for rel in category_list:
            term = rel[0]
            relcount = extracted_text.count(term)
            if relcount:
                relterms[term] = relcount

        num = 0
        # import pdb; pdb.set_trace()
        for term, count in sorted(relterms.items(), key=lambda item: item[1],
                                  reverse=True):
            logger.debug(f"328:WORDMAP {term} {count} {self.wordmap[term]}")

            concept.append({'text': term, 'Reason': self.wordmap[term]})
            num += 1
            if num >= RLIMIT:
                break

        return None

# end of module
