"""
------------------------------------------------------------
File: otp.py

Module: Authentication Models

Purpose:
Store OTP records used by AP Studio Authentication Engine.

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
# OTP Types
# ==========================================================

class OTPType(models.TextChoices):
    """
    Supported OTP types.
    """

    EMAIL_VERIFICATION = (
        "EMAIL_VERIFICATION",
        "Email Verification",
    )

    PASSWORD_RESET = (
        "PASSWORD_RESET",
        "Password Reset",
    )

    LOGIN_VERIFICATION = (
        "LOGIN_VERIFICATION",
        "Login Verification",
    )

    PHONE_VERIFICATION = (
        "PHONE_VERIFICATION",
        "Phone Verification",
    )

    ACCOUNT_UNLOCK = (
        "ACCOUNT_UNLOCK",
        "Account Unlock",
    )


# ==========================================================
# OTP Model
# ==========================================================

class OTP(BaseModel):
    """
    Store One-Time Passwords.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otps",
    )

    otp = models.CharField(
        max_length=10,
    )

    otp_type = models.CharField(
        max_length=30,
        choices=OTPType.choices,
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(
        default=False,
    )

    retry_count = models.PositiveIntegerField(
        default=0,
    )

    maximum_retry = models.PositiveIntegerField(
        default=3,
    )

    class Meta:
        db_table = "aps_otps"

    def __str__(self) -> str:
        return (
            f"{self.user.email}"
            f" | "
            f"{self.otp_type}"
        )