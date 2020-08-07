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

    text = models.CharField(max_length=200)

    location = models.ForeignKey('fixpol.Location', null=True,
        related_name='criteria', on_delete=models.CASCADE)

    impacts = models.ManyToManyField(Impact)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


class Law(models.Model):
    """Summary of legislation resulting from Machine Learning"""

    class Meta:
        app_label = 'fixpol'
        verbose_name_plural = "laws"  # plural of legislation

    title = models.CharField(max_length=200)

    summary = models.CharField(max_length=1000)

    location = models.ForeignKey('fixpol.Location', null=True,
        related_name='laws', on_delete=models.CASCADE)

    impacts = models.ForeignKey('fixpol.Impact', null=True,
        related_name='laws', on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title








