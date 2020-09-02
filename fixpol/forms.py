from django import forms
from fixpol.models import Location, Impact
from .models import Criteria


class SearchForm(forms.ModelForm):
    class Meta:
        model = Criteria
        fields = ('location', 'impacts')

    location = forms.ModelChoiceField(
        queryset=Location.objects.exclude(shortname='world'),
        empty_label='Please select a location'
    )

    impacts = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Impact.objects.all()
    )

    def __init__(self, *args, **kwargs):
        """Specify location and impact pull down menus """
        super(SearchForm, self).__init__(*args, **kwargs)

        # if you want to do just one
        self.fields['location'].error_messages = {
            'required': 'A location must be selected'}
        self.fields['impacts'].error_messages = {
            'required': 'Select one or more impact areas'}
