from django import forms
from django.contrib.auth.models import User
from fixpol.models import Location, Impact
from .models import Criteria

class SearchForm(forms.ModelForm):
    class Meta:
        model = Criteria
        fields = ('location', 'impacts')

    impacts = forms.ModelMultipleChoiceField(
                       widget = forms.CheckboxSelectMultiple,
                       queryset = Impact.objects.all()
                       )
