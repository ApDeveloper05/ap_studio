"""
------------------------------------------------------------
File: login.py

Module: Authentication Forms

Purpose:
Handle user login form.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django import forms

from source.modules.auth.validators.email import EmailValidator


class LoginForm(forms.Form):
    """
    User login form.
    """

    email = forms.EmailField(
        required=True,
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
    )

    def clean_email(self):
        """
        Normalize email.
        """

        email = self.cleaned_data["email"]

        if not EmailValidator.validate_format(email):
            raise forms.ValidationError(
                "Invalid email format."
            )

        return EmailValidator.normalize(email)