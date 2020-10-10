from django import forms
from django.contrib.auth.models import User
from cfc_app.models import Location, Impact
from .models import Profile


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('location', 'impacts')

    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        empty_label='Please select a location'
    )

    impacts = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Impact.objects.all()
    )
