from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class Location(models.Model):
    """A location helps filter which legislation to look at."""

    class Meta:
        app_label = 'fixpol'

    desc = models.CharField(max_length=80)
    shortname = models.CharField(max_length=20)
    hierarchy = models.CharField(max_length=200,unique=True)
    govlevel = models.CharField(max_length=80)
    parent = models.ForeignKey('self', null=True, 
            related_name='locations', on_delete=models.PROTECT)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.desc

class Impact(models.Model):
    """A location helps filter which legislation to look at."""

    class Meta:
        app_label = 'fixpol'

    text = models.CharField(max_length=80, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


class Criteria(models.Model):
    """ Criteria of anonymous or user-profile search """

    class Meta:
        app_label = 'fixpol'
        verbose_name_plural = "criteria"  # plural of criteria

    text = models.CharField(max_length=200, unique=True, null=True, blank=True)

    location = models.ForeignKey('fixpol.Location', null=True,
        related_name='criteria', on_delete=models.CASCADE)

    impacts = models.ManyToManyField(Impact)


    def __str__(self):
        """Return a string representation of the model."""
        return self.text


    def set_text(self):
        crit_text = criteria_string(self.location, self.impacts.all())
        self.text = crit_text
        return self.text


def criteria_string(location, impact_list):
    loc_text = location.hierarchy
    impact_string = impact_seq(impact_list)
    crit_text = loc_text + impact_string
    return crit_text


def find_criteria_id(crit_text):
    crit_id = 0
    #import pdb; pdb.set_trace()
    crits = Criteria.objects.all()
    if crits:
        for crit in crits:
            crit_string=criteria_string(crit.location,
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
        app_label = 'fixpol'
        verbose_name_plural = "laws"  # plural of legislation

    title = models.CharField(max_length=200)

    summary = models.CharField(max_length=1000)

    location = models.ForeignKey('fixpol.Location', null=True,
        related_name='laws', on_delete=models.CASCADE)

    impact = models.ForeignKey('fixpol.Impact', null=True,
        related_name='laws', on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title








