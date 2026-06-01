from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password1', 'password2',
            'preferred_budget',
            'pref_culture', 'pref_adventure', 'pref_nature',
            'pref_beaches', 'pref_nightlife', 'pref_cuisine',
            'pref_wellness', 'pref_urban', 'pref_seclusion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]
        interest_fields = [
            'pref_culture', 'pref_adventure', 'pref_nature',
            'pref_beaches', 'pref_nightlife', 'pref_cuisine',
            'pref_wellness', 'pref_urban', 'pref_seclusion',
        ]
        for field in interest_fields:
            self.fields[field].widget = forms.Select(choices=SCORE_CHOICES)
            self.fields[field].label = field.replace('pref_', '').capitalize()
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'bio', 'avatar',
            'preferred_budget',
            'pref_culture', 'pref_adventure', 'pref_nature',
            'pref_beaches', 'pref_nightlife', 'pref_cuisine',
            'pref_wellness', 'pref_urban', 'pref_seclusion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]
        interest_fields = [
            'pref_culture', 'pref_adventure', 'pref_nature',
            'pref_beaches', 'pref_nightlife', 'pref_cuisine',
            'pref_wellness', 'pref_urban', 'pref_seclusion',
        ]
        for field in interest_fields:
            self.fields[field].widget = forms.Select(choices=SCORE_CHOICES)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
