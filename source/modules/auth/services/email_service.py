"""
------------------------------------------------------------
File: email_service.py

Module: Authentication Services

Purpose:
Handle authentication related emails with full security alerts.

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
                from_email=getattr(settings, "EMAIL_HOST_USER", "noreply@apstudio.com"),
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
            "Your account has been created and verified successfully."
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

        subject = "Verify Your Email - AP Studio"

        message = (
            "Your verification OTP is:\n\n"
            f"{otp}\n\n"
            "This OTP is valid for 15 minutes.\n"
            "Warning: 3 consecutive failed attempts will lock your registration for 48 hours."
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

        subject = "Password Reset - AP Studio"

        message = (
            "Your password reset OTP is:\n\n"
            f"{otp}\n\n"
            "This OTP is valid for 15 minutes.\n"
            "Warning: 3 consecutive failed attempts will freeze your account for 24 hours."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_login_otp_email(
        cls,
        recipient: str,
        otp: str,
    ) -> bool:
        """
        Send 8-digit Login OTP (Emergency Passwordless Access).
        """

        subject = "Your AP Studio Login Code (8-Digit OTP)"

        message = (
            "Hi,\n\n"
            "You requested an emergency Login OTP for your AP Studio account.\n\n"
            f"Your 8-Digit Security Code: {otp}\n\n"
            "This code is strictly confidential and expires in 15 minutes.\n"
            "Do NOT share this code with anyone.\n"
            "Warning: 3 consecutive failed attempts will freeze your account for 24 hours."
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
            "because of multiple failed password attempts."
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

    @classmethod
    def send_registration_blocked_alert(
        cls,
        recipient: str,
        hours: int = 48,
    ) -> bool:
        """
        Alert user that registration with this email is blocked due to 3 failed OTPs.
        """

        subject = f"SECURITY ALERT: Registration Temporarily Blocked ({hours} Hours)"

        message = (
            "Security Alert,\n\n"
            f"Registration using email '{recipient}' has been temporarily blocked for {hours} hours "
            "due to 3 consecutive failed OTP attempts.\n\n"
            "If this was you, please wait for the countdown timer to expire before re-registering.\n"
            "If you did NOT attempt this signup, someone may be attempting to misuse your email address."
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_account_seized_alert(
        cls,
        recipient: str,
        hours: int = 24,
    ) -> bool:
        """
        Alert user that account has been seized/frozen for 24h due to 3 failed OTPs.
        """

        subject = f"CRITICAL SECURITY ALERT: AP Studio Account Frozen for {hours} Hours"

        message = (
            "CRITICAL SECURITY ALERT,\n\n"
            "Your AP Studio account has been temporarily FROZEN and all active sessions across all devices "
            f"have been terminated immediately for the next {hours} hours.\n\n"
            "Reason: 3 consecutive failed OTP attempts were detected on your account.\n\n"
            f"Once the {hours}-hour safety period completes, you will receive an automated recovery link "
            "to re-verify your identity and safely restore dashboard access.\n\n"
            "AP Studio Security Engine"
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_unfreeze_recovery_email(
        cls,
        recipient: str,
        recovery_url: str,
    ) -> bool:
        """
        Send automated recovery notification once freeze period expires.
        """

        subject = "AP Studio: Your Security Freeze Has Ended - Re-Verify Account"

        message = (
            "Hi,\n\n"
            "Good news! The security freeze period on your AP Studio account has completed.\n\n"
            "To restore full access to your account and re-activate your dashboard, click the link below:\n\n"
            f"{recovery_url}\n\n"
            "You will be asked to complete a fresh verification step to safely re-claim your account.\n\n"
            "AP Studio Security Engine"
        )

        return cls.send_email(
            subject,
            message,
            recipient,
        )

    @classmethod
    def send_admin_security_alert(
        cls,
        title: str,
        details: str,
    ) -> bool:
        """
        Notify System Administrator of high-priority security incidents.
        """

        subject = f"[AP Studio Admin Security Alert] {title}"

        message = (
            "AP STUDIO ADMIN NOTIFICATION\n"
            "============================\n\n"
            f"Incident: {title}\n\n"
            f"Details:\n{details}\n\n"
            "Check AP Studio security monitoring logs for full request metadata."
        )

        admin_email = getattr(settings, "ADMIN_ALERT_EMAIL", getattr(settings, "EMAIL_HOST_USER", "admin@apstudio.com"))

        return cls.send_email(
            subject,
            message,
            admin_email,
        )
