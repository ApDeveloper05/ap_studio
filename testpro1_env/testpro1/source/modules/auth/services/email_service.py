"""
------------------------------------------------------------
File: email_service.py

Module: Authentication Services

Purpose:
Handle authentication related emails.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.conf import settings
from django.core.mail import send_mail


class EmailService:
    """
    Handle email delivery.
    """

    @staticmethod
    def send_email(
        subject: str,
        message: str,
        recipient: str,
    ) -> bool:
        """
        Send email.
        """

        try:

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient],
                fail_silently=False,
            )

            return True

        except Exception:

            return False

    @classmethod
    def send_welcome_email(
        cls,
        recipient: str,
    ) -> bool:
        """
        Send welcome email.
        """

        subject = "Welcome to AP Studio"

        message = (
            "Welcome to AP Studio.\n\n"
            "Your account has been created successfully."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_verification_email(
        cls,
        recipient: str,
        otp: str,
    ) -> bool:
        """
        Send email verification OTP.
        """

        subject = "Verify Your Email"

        message = (
            "Your verification OTP is:\n\n"
            f"{otp}\n\n"
            "This OTP is valid for 15 minutes."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_password_reset_email(
        cls,
        recipient: str,
        otp: str,
    ) -> bool:
        """
        Send password reset OTP.
        """

        subject = "Password Reset"

        message = (
            "Your password reset OTP is:\n\n"
            f"{otp}\n\n"
            "This OTP is valid for 15 minutes."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_account_locked_email(
        cls,
        recipient: str,
    ) -> bool:
        """
        Notify account lock.
        """

        subject = "Account Locked"

        message = (
            "Your account has been temporarily locked "
            "because of multiple failed login attempts."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_account_unlocked_email(
        cls,
        recipient: str,
    ) -> bool:
        """
        Notify account unlock.
        """

        subject = "Account Unlocked"

        message = (
            "Your account has been unlocked successfully."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )