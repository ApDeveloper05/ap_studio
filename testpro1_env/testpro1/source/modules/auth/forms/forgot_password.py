"""
------------------------------------------------------------
File: forgot_password.py

Module: Authentication Forms

Purpose:
Handle forgot password form.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django import forms

from source.modules.auth.validators.email import EmailValidator


class ForgotPasswordForm(forms.Form):
    """
    Forgot password form.
    """

    email = forms.EmailField(
        required=True,
    )

    def clean_email(self):
        """
        Validate email.
        """

        email = self.cleaned_data["email"]

        if not EmailValidator.validate_format(email):
            raise forms.ValidationError(
                "Invalid email format."
            )

        return EmailValidator.normalize(email)