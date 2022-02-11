#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cfc_app/models.py -- Database ORM models used by cfc_app.

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import datetime as DT
import logging

# Django and other third-party imports
from django.db import models
from django.conf import settings

LEFT_CORNER = u"\u2514\u2500\u2002"
LEFT_PAD = u"\u2002\u2002\u2002\u2002"

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

##############################################
# Support functions must come first
##############################################


def get_default_law_key():
    """ Default key needs to be unique timestamp until changed """
    today = str(DT.datetime.now())
    key = today[5:25]
    return key


# Create your models here.


class Location(models.Model):
    """ A location helps filter which legislation to look at. """

    class Meta:
        """ set ordering method """
        app_label = 'cfc_app'
        ordering = ['hierarchy']

    longname = models.CharField(max_length=80)
    shortname = models.CharField(max_length=20)
    legiscan_id = models.IntegerField()
    hierarchy = models.CharField(max_length=200)
    govlevel = models.CharField(max_length=80)
    parent = models.ForeignKey('self', null=True,
                               related_name='locations',
                               on_delete=models.PROTECT)
    date_added = models.DateTimeField(auto_now_add=True)

    def padding(self):
        """ Return a string representation of the model. """
        level = self.hierarchy.count(".")
        padding = ''
        if level > 1:
            padding = LEFT_PAD*(level-2) + LEFT_CORNER
        return padding

    def __str__(self):
        """ Return a string representation of the model. """
        loc_string = self.padding() + self.longname
        return loc_string

    @staticmethod
    def load_defaults():
        """ set location defaults if cfc_seed.json not used

        The 'world' entry points to itself, so cannot be added using
        traditional Django administration.  To create it here, we have
        to create an entry with no parent, save it, then set the parent_id
        to 1.  This only works if the AUTOINCREMENT sequence is set to zero,
        for an empty database, or reset to zero if entries deleted.
        """

        world = Location()
        world.longname = 'world'
        world.shortname = 'world'
        world.legiscan_id = 0
        world.hierarchy = 'world'
        world.govlevel = 'world'
        world.save()
        world.parent = world
        world.save()

        # The concept of ancestor-search is confusing, so we create a few
        # entries (usa, arizona, ohio) so people can understand the structure
        # Note the legiscan_id is only needed for States in the United States.

        usa = Location(longname='United States', shortname='usa',
                       legiscan_id=52, hierarchy='world.usa', 
                       govlevel='country')
        usa.parent = world
        usa.save()

        arizona = Location(longname='Arizona, USA', shortname='az',
                           legiscan_id=3, hierarchy='world.usa.az', 
                           govlevel='state')
        arizona.parent = usa
        arizona.save()

        ohio = Location(longname='Ohio, USA', shortname='oh', legiscan_id=35,
                        hierarchy='world.usa.oh', govlevel='state')
        ohio.parent = usa
        ohio.save()
        return None

class Impact(models.Model):
    """A location helps filter which legislation to look at."""

    class Meta:
        """ set ordering method """
        app_label = 'cfc_app'
        ordering = ['date_added']

    iname = models.CharField(max_length=80, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.iname

    @staticmethod
    def load_defaults():
        """ load defaults for Impacts.

        The 'None' option allows legislation to be hidden from all
        searches.  This is useful for legislation that is fetched
        through automation but mis-classified.  Setting impact=None
        will prevent automation from fetching updated versions of this.

        Impacts are displayed in the order they are added in this table.
        Any new impacts added will appear at the bottom of the list.
        """

        default_impacts = ['None', 'Healthcare', 'Safety', 'Environment',
                           'Transportation', 'Jobs']
        for entry in default_impacts:
            new_impact = Impact()
            new_impact.iname = entry
            new_impact.save()
        return None


class Criteria(models.Model):
    """ Criteria of anonymous or user-profile search """

    class Meta:
        """ set plurality """
        app_label = 'cfc_app'
        verbose_name_plural = "criteria"  # plural of criteria

    crtext = models.CharField(max_length=200, null=True, blank=True)

    location = models.ForeignKey('cfc_app.Location', null=True,
                                 related_name='criteria',
                                 on_delete=models.CASCADE)

    impacts = models.ManyToManyField(Impact)

    def __str__(self):
        """Return a string representation of the model."""
        key = str(self.id)
        if self.crtext:
            key += ':' + self.crtext
        return key

    def set_text(self):
        """ Combine location and impacts into a single text string """
        crit_text = criteria_string(self.location, self.impacts.all())
        self.crtext = crit_text
        return self.crtext


def criteria_string(location, impact_list):
    """ Combine location and impacts into a single text string """
    loc_text = location.hierarchy
    impact_string = impact_seq(impact_list)
    crit_text = loc_text + impact_string
    return crit_text


def find_criteria_id(crit_text):
    """ Find criteria entry that matches location and impacts """
    crit_id = 0
    crits = Criteria.objects.all()
    if crits:
        for crit in crits:
            crit_string = criteria_string(crit.location,
                                          crit.impacts.all())
            if crit_string == crit_text:
                crit_id = crit.id
                break

    return crit_id


def impact_seq(impact_list):
    """String together all selected impacts in impact_list."""
    impact_string = ''
    connector = '-'
    for impact in impact_list:
        impact_string += connector + impact.iname.strip()

    return impact_string


class Law(models.Model):
    """Summary of legislation resulting from Machine Learning"""

    class Meta:
        """ set plurality and ordering """
        app_label = 'cfc_app'
        verbose_name_plural = "laws"  # plural of legislation
        ordering = ['key']

    key = models.CharField(max_length=25, null=False,
                           unique=True, default=get_default_law_key)

    bill_id = models.CharField(max_length=15, null=True)
    doc_date = models.CharField(max_length=10, null=True)

    title = models.TextField(max_length=200)

    summary = models.TextField(max_length=1000)

    location = models.ForeignKey('cfc_app.Location', null=True,
                                 related_name='laws', on_delete=models.CASCADE)

    impact = models.ForeignKey('cfc_app.Impact', null=True,
                               related_name='laws', on_delete=models.CASCADE)

    relevance = models.TextField(max_length=800, null=True)

    cite_url = models.URLField(max_length=200, null=True)

    def __str__(self):
        """Return a string representation of the model."""
        law_string = str(self.title)
        law_length = len(law_string)
        if law_length > 50:
            law_string = law_string[:50]
            law_string = law_string.rsplit(' ', 1)[0]
            if len(law_string) < law_length:
                law_string += " ..."
        law_string = self.key + ' ' + law_string
        return law_string


class Hash(models.Model):
    """ Track hash codes of files stored in FOB_Storage """

    class Meta:
        """ set plurality and ordering method """

        app_label = 'cfc_app'
        verbose_name_plural = "hashcodes"  # plural of hash
        ordering = ['item_name']
        unique_together = ('item_name', 'fob_method',)

    item_name = models.CharField(max_length=255, null=False)
    fob_method = models.CharField(max_length=6, null=False)
    generated_date = models.DateField(null=False)
    hashcode = models.CharField(max_length=32, null=False)
    objsize = models.PositiveIntegerField(null=False)
    legdesc = models.CharField(max_length=255, null=True)

    def __str__(self):
        """Return a string representation of the model."""
        legdesc = '{} ({})'.format(self.item_name, self.fob_method)
        return legdesc

    @staticmethod
    def find_item_name(name, mode=settings.FOB_METHOD):
        """ get item if exists, None if not """

        record = Hash.objects.filter(item_name=name,
                                     fob_method=mode).first()
        return record


def delete_if_exists(name, mode=settings.FOB_METHOD):
    """ delete item if exists """

    Hash.objects.filter(item_name=name, fob_method=mode).delete()
    return None


def save_source_hash(bill_hash, detail):
    """ Save hashcode to cfc_app_hash table """

    if bill_hash is None:
        bill_hash = Hash()
        bill_hash.item_name = detail.bill_name
        bill_hash.fob_method = settings.FOB_METHOD
        bill_hash.legdesc = detail.title
        bill_hash.generated_date = detail.doc_date
        bill_hash.hashcode = detail.hashcode
        bill_hash.objsize = detail.doc_size
        logger.debug(f"302:INSERT cfc_app_law: {detail.bill_name}")
        bill_hash.save()

    else:
        bill_hash.generated_date = detail.doc_date
        bill_hash.hashcode = detail.hashcode
        bill_hash.objsize = detail.doc_size
        logger.debug(f"309:UPDATE cfc_app_law: {detail.bill_name}")
        bill_hash.save()

    return None


def save_entry_to_hash(session_name, entry):
    """ Save hashcode in cfc_app_hash database table """

    find_hash = Hash.find_item_name(session_name)
    if find_hash is None:
        find_hash = Hash()
        find_hash.item_name = session_name
        find_hash.fob_method = settings.FOB_METHOD
        find_hash.legdesc = entry['session_name']
        find_hash.generated_date = entry['dataset_date']
        find_hash.hashcode = entry['dataset_hash']
        find_hash.objsize = entry['dataset_size']
        find_hash.save()

    else:
        find_hash.generated_date = entry['dataset_date']
        find_hash.hashcode = entry['dataset_hash']
        find_hash.objsize = entry['dataset_size']
        find_hash.save()

    return None

# end of module
