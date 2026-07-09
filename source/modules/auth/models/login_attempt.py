"""
------------------------------------------------------------
File: login_attempt.py

Module: Authentication Models

Purpose:
Track user login attempts for security monitoring.

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
# Login Attempt Model
# ==========================================================

class LoginAttempt(BaseModel):
    """
    Store login attempt history.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_attempts",
        blank=True,
        null=True,
    )

    email = models.EmailField()

    ip_address = models.GenericIPAddressField()

    user_agent = models.TextField()

    is_successful = models.BooleanField(
        default=False,
    )

    failure_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "aps_login_attempts"

    def __str__(self) -> str:
        return self.email