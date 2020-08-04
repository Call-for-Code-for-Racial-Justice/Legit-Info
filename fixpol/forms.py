from django import forms

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('locatation', 'impacts')


