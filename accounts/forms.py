from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
class RegistrationForm(UserCreationForm):
    agency_name = forms.CharField(max_length=180)
    city = forms.CharField(max_length=100,initial='Dar es Salaam')
    email = forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username','first_name','last_name','email','agency_name','city','password1','password2']
