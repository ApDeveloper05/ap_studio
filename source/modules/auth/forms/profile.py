"""
------------------------------------------------------------
File: profile.py

Module: Authentication Forms

Purpose:
Handle profile update form.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django import forms


class ProfileForm(forms.Form):
    """
    User profile form.
    """

    first_name = forms.CharField(
        max_length=100,
        required=True,
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
    )

    profile_picture = forms.ImageField(
        required=False,
    )

    address = forms.CharField(
        widget=forms.Textarea,
        required=False,
    )

    city = forms.CharField(
        max_length=100,
        required=False,
    )

    state = forms.CharField(
        max_length=100,
        required=False,
    )

    country = forms.CharField(
        max_length=100,
        required=False,
    )

    postal_code = forms.CharField(
        max_length=20,
        required=False,
    )