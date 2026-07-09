"""
------------------------------------------------------------
File: email_service.py

Module: Authentication Services

Purpose:
Handle email delivery for AP Studio Authentication.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""


class EmailService:
    """
    Handle all authentication related emails.
    """

    def send_welcome_email(self) -> None:
        """
        Send welcome email.
        """
        pass

    def send_verification_email(self) -> None:
        """
        Send email verification link or OTP.
        """
        pass

    def send_password_reset_email(self) -> None:
        """
        Send password reset email.
        """
        pass

    def send_account_locked_email(self) -> None:
        """
        Notify user about account lock.
        """
        pass

    def send_account_unlocked_email(self) -> None:
        """
        Notify user after account unlock.
        """
        pass