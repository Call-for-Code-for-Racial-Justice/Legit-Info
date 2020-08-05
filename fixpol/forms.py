from django import forms
from django.db import models
from .models import Location, Impact

class SubmitForm(forms.Form): 
    loc_id = models.IntegerField()
    impact_id = models.IntegerField()

