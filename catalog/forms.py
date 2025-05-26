from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
import re

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Разрешены только латинские буквы, цифры и подчёркивания.")
        return username

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput)
