"""
------------------------------------------------------------
File: otp_service.py

Module: Authentication Services

Purpose:
Generate and verify One-Time Passwords with automated 3-strike
security triggers (48h signup block & 24h account freeze).
Supports standard 6-digit OTP and 8-digit emergency Login OTP.

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
    Handle OTP operations with automated security triggers.
    """

    OTP_LENGTH = getattr(settings, "OTP_LENGTH", 6)
    LOGIN_OTP_LENGTH = getattr(settings, "LOGIN_OTP_LENGTH", 8)
    OTP_EXPIRY_MINUTES = getattr(settings, "OTP_EXPIRY_MINUTES", 15)
    OTP_MAX_RETRY = getattr(settings, "OTP_MAX_RETRY", 3)

    @classmethod
    def generate(
        cls,
        user: User,
        otp_type: OTPType,
        length: int | None = None,
    ) -> OTP:
        """
        Generate and store a new OTP.
        Emergency Login OTP defaults to 8 digits for maximum security.
        """

        # Invalidate previous active OTPs of same type
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False,
        ).update(
            expires_at=timezone.now(),
        )

        if length is None:
            if otp_type == OTPType.LOGIN_VERIFICATION:
                length = cls.LOGIN_OTP_LENGTH
            else:
                length = cls.OTP_LENGTH

        otp = "".join(
            str(secrets.randbelow(10))
            for _ in range(length)
        )

        return OTP.objects.create(
            user=user,
            otp=otp,
            otp_type=otp_type,
            expires_at=timezone.now()
            + timedelta(minutes=cls.OTP_EXPIRY_MINUTES),
            maximum_retry=cls.OTP_MAX_RETRY,
        )

    @classmethod
    def verify(
        cls,
        otp_object: OTP,
        entered_otp: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[bool, str]:
        """
        Verify OTP and automatically trigger security strikes.
        Returns tuple (success: bool, status_code: str).
        """

        # Circular import guard
        from source.modules.auth.services.security_service import SecurityService

        if otp_object.is_verified:
            return False, "ALREADY_VERIFIED"

        if timezone.now() > otp_object.expires_at:
            return False, "EXPIRED"

        if otp_object.retry_count >= otp_object.maximum_retry:
            return False, "MAX_RETRY_EXCEEDED"

        if otp_object.otp != entered_otp.strip():

            otp_object.retry_count += 1
            otp_object.save(update_fields=["retry_count"])

            # 🚨 3rd STRIKE SECURITY TRIGGER
            if otp_object.retry_count >= otp_object.maximum_retry:

                # Strike A: Signup Verification -> 48h Email Lock
                if otp_object.otp_type == OTPType.EMAIL_VERIFICATION:
                    SecurityService.block_registration(
                        email=otp_object.user.email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                    return False, "REGISTRATION_BLOCKED_48H"

                # Strike B: Login / Password Reset -> 24h Account Seizure + Session Kill
                if otp_object.otp_type in (
                    OTPType.LOGIN_VERIFICATION,
                    OTPType.PASSWORD_RESET,
                    OTPType.ACCOUNT_UNLOCK,
                ):
                    SecurityService.seize_account(
                        user=otp_object.user,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        reason="3_FAILED_OTP_ATTEMPTS",
                    )
                    return False, "ACCOUNT_SEIZED_24H"

                return False, "MAX_RETRY_EXCEEDED"

            remaining = otp_object.maximum_retry - otp_object.retry_count
            return False, f"INVALID_OTP_{remaining}_ATTEMPTS_LEFT"

        # Success!
        otp_object.is_verified = True
        otp_object.save(update_fields=["is_verified"])

        return True, "VERIFIED"

    @staticmethod
    def expire(
        otp_object: OTP,
    ) -> None:
        """
        Force expire an OTP.
        """

        otp_object.expires_at = timezone.now()
        otp_object.save(update_fields=["expires_at"])
