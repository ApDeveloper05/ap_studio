"""
------------------------------------------------------------
File: profile.py

Module: Authentication Models

Purpose:
Store additional user profile information.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.db import models

from source.modules.auth.models.base import BaseModel
from source.modules.auth.models.user import User


# ==========================================================
# User Profile Model
# ==========================================================

class Profile(BaseModel):
    """
    Store user profile information.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )

    gender = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "aps_profiles"

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"