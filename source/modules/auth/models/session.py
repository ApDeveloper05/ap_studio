"""
------------------------------------------------------------
File: session.py

Module: Authentication Models

Purpose:
Store active user sessions.

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
# Session Model
# ==========================================================

class Session(BaseModel):
    """
    Store authenticated user sessions.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    session_token = models.CharField(
        max_length=255,
        unique=True,
    )

    ip_address = models.GenericIPAddressField()

    user_agent = models.TextField()

    expires_at = models.DateTimeField()

    last_activity = models.DateTimeField()

    is_expired = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "aps_sessions"

    def __str__(self) -> str:
        return self.user.email