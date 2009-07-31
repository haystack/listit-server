from django import forms
import re
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import eyebrowse.models


class RegistrationForm(forms.Form):
    username = forms.CharField(label='Username', max_length=30)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput()
        )
    password2 = forms.CharField(
        label='Password (Again)',
        widget=forms.PasswordInput()
        )
    
    def clean_password2(self):
        if 'password1' in self.cleaned_data:
            password1 = self.cleaned_data['password1']
            password2 = self.cleaned_data['password2']
            if password1 == password2:
                return password2
        raise forms.ValidationError('Passwords do not match.')

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError('Username can only contain alphanumeric characters and the underscore.')
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError('Username is already taken.')

class ProfileSaveForm(forms.Form):
#     first_name = forms.CharField(
#         label='First Name',
#         widget=forms.TextInput(attrs={'size': 250}), 
#         required=False
#         )
#     last_name = forms.CharField(
#         label='Last Name',
#         widget=forms.TextInput(attrs={'size': 250}), 
#         required=False
#         )
    email = forms.EmailField(
        label='Email',
        widget=forms.TextInput(attrs={'size': 250}), 
        required=False
        )
    location = forms.CharField(
        label='Location',
        widget=forms.TextInput(attrs={'size': 250}), 
        required=False
        )
    tags = forms.CharField(
        label='Tags',
        widget=forms.TextInput(attrs={'size': 250}), 
        required=False
        )
    homepage = forms.URLField(
        label='Homepage',
        widget=forms.TextInput(attrs={'size': 250}),
        verify_exists=False,
        required=False
        )
    birthdate = forms.DateTimeField(
        label='Birthdate ie: 10/25/86',
        widget=forms.DateTimeInput(attrs={'size': 250}), 
        required=False
        )
    photo = forms.ImageField(
        label='Profile Photo',
        widget=forms.FileInput(attrs={'size': 16}),
        required=False
        )
    gender = forms.TypedChoiceField(
        label='Gender',
        widget = forms.RadioSelect(),
        choices=eyebrowse.models.GENDER_CHOICES, 
        required=False
        )

class PrivacySaveForm(forms.Form):
    exposure = forms.TypedChoiceField(
        label='Exposure',
        widget = forms.RadioSelect(),
        choices=eyebrowse.models.EXPOSURE_CHOICES, 
        required=True
        )
    listmode = forms.TypedChoiceField(
        label='List Mode',
        widget = forms.RadioSelect(),
        choices=eyebrowse.models.LOGGING_LIST_MODE, 
        required=True
        )

class LabelSaveForm(forms.Form):
    label = forms.CharField(
        label='Tags',
        widget=forms.TextInput(attrs={'size': 250}), 
        required=False
        )

class FriendInviteForm(forms.Form):
    name = forms.CharField(label='Friend\'s Name')
    email = forms.EmailField(label='Friend\'s Email')

class UserSearchForm(forms.Form):
    query = forms.CharField(
        label='Enter a keyword to search users',
        widget=forms.TextInput(attrs={'size': 32})
        )

class GroupSearchForm(forms.Form):
    query = forms.CharField(
        label='Enter a keyword to search groups',
        widget=forms.TextInput(attrs={'size': 32})
        )
        
class PageSearchForm(forms.Form):
    query = forms.CharField(
        label='Enter a keyword to search webpages',
        widget=forms.TextInput(attrs={'size': 32})
        )
