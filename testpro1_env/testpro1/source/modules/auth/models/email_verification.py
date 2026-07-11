"""
------------------------------------------------------------
File: email_verification.py

Module: Authentication Models

Purpose:
Store email verification history.

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
# Email Verification Model
# ==========================================================

class EmailVerification(BaseModel):
    """
    Store email verification records.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )

    email = models.EmailField()

    verification_token = models.CharField(
        max_length=255,
        unique=True,
    )

    expires_at = models.DateTimeField()

    verified_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "aps_email_verifications"

    def __str__(self) -> str:
        return self.email