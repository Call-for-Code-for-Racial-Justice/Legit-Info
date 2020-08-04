from django import forms
from django.contrib.auth.models import User
from fixpol.models import Location, Impact
from .models import Profile

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('prof_location', 'prof_impacts')


