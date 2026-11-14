"""
------------------------------------------------------------
File: security.py

Module: Authentication Models

Purpose:
Track blocked registrations and seized accounts for AP Studio
enterprise security engine (48h signup block & 24h account seizure).

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from datetime import timedelta
import secrets

from django.db import models
from django.utils import timezone

from source.modules.auth.models.base import BaseModel
from source.modules.auth.models.user import User


# ==========================================================
# Blocked Registration (48-Hour Hard Block)
# ==========================================================

class BlockedRegistration(BaseModel):
    """
    Store temporary registration blocks.
    Triggered when a user enters wrong OTP 3 times during signup.
    Blocked for 48 hours.
    """

    DEFAULT_BLOCK_HOURS = 48

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
    )

    blocked_until = models.DateTimeField(
        db_index=True,
    )

    reason = models.CharField(
        max_length=255,
        default="3_FAILED_SIGNUP_OTP_ATTEMPTS",
    )

    failure_count = models.PositiveIntegerField(
        default=3,
    )

    class Meta:
        db_table = "aps_blocked_registrations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} | Blocked until: {self.blocked_until}"

    @property
    def is_active_block(self) -> bool:
        """
        Check if the block is currently active.
        """
        return timezone.now() < self.blocked_until

    @property
    def remaining_seconds(self) -> int:
        """
        Calculate remaining seconds for live UI countdown timer.
        """
        if not self.is_active_block:
            return 0
        delta = self.blocked_until - timezone.now()
        return max(0, int(delta.total_seconds()))

    @property
    def remaining_formatted(self) -> str:
        """
        Return formatted remaining time e.g., '47h 59m 30s'.
        """
        seconds = self.remaining_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"


# ==========================================================
# Seized Account (24-Hour Global Freeze)
# ==========================================================

class SeizedAccount(BaseModel):
    """
    Store 24-hour account seizures.
    Triggered when 3 wrong OTP attempts occur on login / reset password.
    Destroys all active sessions across all devices and freezes the user.
    """

    DEFAULT_SEIZE_HOURS = 24

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="seizures",
    )

    email = models.EmailField(
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
    )

    seized_until = models.DateTimeField(
        db_index=True,
    )

    reason = models.CharField(
        max_length=255,
        default="3_FAILED_OTP_ATTEMPTS",
    )

    recovery_token = models.CharField(
        max_length=128,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    recovery_email_sent = models.BooleanField(
        default=False,
    )

    is_recovered = models.BooleanField(
        default=False,
    )

    recovered_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "aps_seized_accounts"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} | Seized until: {self.seized_until}"

    @property
    def is_currently_seized(self) -> bool:
        """
        Check if account is currently frozen.
        """
        if self.is_recovered:
            return False
        return timezone.now() < self.seized_until

    @property
    def remaining_seconds(self) -> int:
        """
        Calculate remaining seconds for live countdown timer.
        """
        if not self.is_currently_seized:
            return 0
        delta = self.seized_until - timezone.now()
        return max(0, int(delta.total_seconds()))

    @property
    def remaining_formatted(self) -> str:
        """
        Return formatted remaining time e.g., '23h 45m 12s'.
        """
        seconds = self.remaining_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"

    def generate_recovery_token(self) -> str:
        """
        Generate a cryptographically secure token for automated recovery email.
        """
        token = secrets.token_urlsafe(48)
        self.recovery_token = token
        self.save(update_fields=["recovery_token"])
        return token
