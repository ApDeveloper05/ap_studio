"""
------------------------------------------------------------
File: otp_service.py

Module: Authentication Services

Purpose:
Generate and verify One-Time Passwords.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from datetime import timedelta
import secrets

from django.utils import timezone

from source.core.config import settings
from source.modules.auth.models.otp import OTP
from source.modules.auth.models.otp import OTPType
from source.modules.auth.models.user import User


class OTPService:
    """
    Handle OTP operations.
    """

    OTP_LENGTH = settings.OTP_LENGTH

    OTP_EXPIRY_MINUTES = settings.OTP_EXPIRY_MINUTES

    OTP_MAX_RETRY = settings.OTP_MAX_RETRY

    @classmethod
    def generate(
        cls,
        user: User,
        otp_type: OTPType,
    ) -> OTP:
        """
        Generate and store a new OTP.
        """

        # Invalidate previous active OTPs
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False,
        ).update(
            expires_at=timezone.now(),
        )

        otp = "".join(
            str(secrets.randbelow(10))
            for _ in range(cls.OTP_LENGTH)
        )

        return OTP.objects.create(
            user=user,
            otp=otp,
            otp_type=otp_type,
            expires_at=timezone.now()
            + timedelta(minutes=cls.OTP_EXPIRY_MINUTES),
            maximum_retry=cls.OTP_MAX_RETRY,
        )

    @staticmethod
    def verify(
        otp_object: OTP,
        entered_otp: str,
    ) -> bool:
        """
        Verify OTP.
        """

        if otp_object.is_verified:
            return False

        if timezone.now() > otp_object.expires_at:
            return False

        if otp_object.retry_count >= otp_object.maximum_retry:
            return False

        if otp_object.otp != entered_otp:

            otp_object.retry_count += 1

            otp_object.save(
                update_fields=[
                    "retry_count",
                ]
            )

            return False

        otp_object.is_verified = True

        otp_object.save(
            update_fields=[
                "is_verified",
            ]
        )

        return True

    @staticmethod
    def expire(
        otp_object: OTP,
    ) -> None:
        """
        Force expire an OTP.
        """

        otp_object.expires_at = timezone.now()

        otp_object.save(
            update_fields=[
                "expires_at",
            ]
        )