from django.db import models
from datetime import datetime

LEFT_CORNER = u"\u2514\u2500\u2002"
LEFT_PAD = u"\u2002\u2002\u2002\u2002"

# default to 1 day from now
# import pdb; pdb.set_trace()  -- use this for debugging


def get_default_law_key():
    """ Default key needs to be unique timestamp until changed """
    x = str(datetime.now())
    key = x[5:25]
    return key

# Create your models here.


class Location(models.Model):
    """A location helps filter which legislation to look at."""

    class Meta:
        app_label = 'cfc_app'
        ordering = ['hierarchy']

    desc = models.CharField(max_length=80)
    shortname = models.CharField(max_length=20)
    legiscan_id = models.IntegerField()
    hierarchy = models.CharField(max_length=200)
    govlevel = models.CharField(max_length=80)
    parent = models.ForeignKey('self', null=True,
                               related_name='locations',
                               on_delete=models.PROTECT)
    date_added = models.DateTimeField(auto_now_add=True)

    def padding(self):
        """Return a string representation of the model."""
        level = self.hierarchy.count(".")
        padding = ''
        if level > 1:
            padding = LEFT_PAD*(level-2) + LEFT_CORNER
        return padding

    def __str__(self):
        """Return a string representation of the model."""
        loc_string = self.padding() + self.desc
        return loc_string


class Impact(models.Model):
    """A location helps filter which legislation to look at."""

    class Meta:
        app_label = 'cfc_app'
        ordering = ['date_added']

    text = models.CharField(max_length=80, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


class Criteria(models.Model):
    """ Criteria of anonymous or user-profile search """

    class Meta:
        app_label = 'cfc_app'
        verbose_name_plural = "criteria"  # plural of criteria

    text = models.CharField(max_length=200, null=True, blank=True)

    location = models.ForeignKey('cfc_app.Location', null=True,
                                 related_name='criteria',
                                 on_delete=models.CASCADE)

    impacts = models.ManyToManyField(Impact)

    def __str__(self):
        """Return a string representation of the model."""
        key = str(self.id)
        if self.text:
            key += ':' + self.text
        return key

    def set_text(self):
        """ Combine location and impacts into a single text string """
        crit_text = criteria_string(self.location, self.impacts.all())
        self.text = crit_text
        return self.text


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
        impact_string += connector + impact.text.strip()

    return impact_string


class Law(models.Model):
    """Summary of legislation resulting from Machine Learning"""

    class Meta:
        app_label = 'cfc_app'
        verbose_name_plural = "laws"  # plural of legislation
        ordering = ['key']

    key = models.CharField(max_length=20, null=False,
                           unique=True, default=get_default_law_key)

    bill_id = models.CharField(max_length=15, null=True)
    doc_date = models.CharField(max_length=10, null=True)

    title = models.CharField(max_length=200)

    summary = models.CharField(max_length=1000)

    location = models.ForeignKey('cfc_app.Location', null=True,
                                 related_name='laws', on_delete=models.CASCADE)

    impact = models.ForeignKey('cfc_app.Impact', null=True,
                               related_name='laws', on_delete=models.CASCADE)

    relevance = models.CharField(max_length=250, null=True)

    def __str__(self):
        """Return a string representation of the model."""
        law_length = len(self.title)
        law_string = self.title
        if law_length > 50:
            law_string = self.title[:50]
            law_string = law_string.rsplit(' ', 1)[0]
            if len(law_string) < law_length:
                law_string += " ..."
        law_string = self.key + ' ' + law_string
        return law_string

class Hash(models.Model):
    """ Track hash codes of files stored in FOB_Storage """

    class Meta:
        app_label = 'cfc_app'
        verbose_name_plural = "hashcodes"  # plural of hash
        ordering = ['item_name']   
        unique_together = ('item_name', 'fob_method',)

    item_name = models.CharField(max_length=255, null=False)
    fob_method = models.CharField(max_length=6, null=False)
    generated_date = models.DateField(null=False)
    hashcode = models.CharField(max_length=32, null=False)
    size = models.PositiveIntegerField(null=False)
    desc = models.CharField(max_length=255, null=True)

    def __str__(self):
        """Return a string representation of the model."""
        desc = '{} ({})'.format(self.item_name, self.fob_method)
        return desc
