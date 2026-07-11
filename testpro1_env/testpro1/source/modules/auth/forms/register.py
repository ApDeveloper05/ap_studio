"""
------------------------------------------------------------
File: register.py

Module: Authentication Forms

Purpose:
Handle user registration form.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django import forms

from source.modules.auth.validators.email import EmailValidator
from source.modules.auth.validators.password import PasswordValidator


class RegisterForm(forms.Form):
    """
    User registration form.
    """

    first_name = forms.CharField(
        max_length=100,
        required=True,
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
    )

    email = forms.EmailField(
        required=True,
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
    )

    role_name = forms.CharField(
        required=True,
    )

    def clean_email(self):
        """
        Validate email.
        """

        email = self.cleaned_data["email"]

        valid, message = EmailValidator.validate(email)

        if not valid:
            raise forms.ValidationError(message)

        return EmailValidator.normalize(email)

    def clean_password(self):
        """
        Validate password.
        """

        password = self.cleaned_data["password"]

        valid, message = PasswordValidator.validate(password)

        if not valid:
            raise forms.ValidationError(message)

        return password

    def clean(self):
        """
        Validate password confirmation.
        """

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm_password = cleaned_data.get(
            "confirm_password"
        )

        if password and confirm_password:

            valid, message = (
                PasswordValidator.confirm(
                    password,
                    confirm_password,
                )
            )

            if not valid:
                raise forms.ValidationError(message)

        return cleaned_data