"""
------------------------------------------------------------
File: reset_password.py

Module: Authentication Forms

Purpose:
Handle password reset form.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django import forms

from source.modules.auth.validators.otp import OTPValidator
from source.modules.auth.validators.password import PasswordValidator


class ResetPasswordForm(forms.Form):
    """
    Reset password form.
    """

    otp = forms.CharField(
        max_length=6,
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

    def clean_otp(self):
        """
        Validate OTP.
        """

        otp = self.cleaned_data["otp"]

        valid, message = OTPValidator.validate(otp)

        if not valid:
            raise forms.ValidationError(message)

        return OTPValidator.normalize(otp)

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

            valid, message = PasswordValidator.confirm(
                password,
                confirm_password,
            )

            if not valid:
                raise forms.ValidationError(message)

        return cleaned_data