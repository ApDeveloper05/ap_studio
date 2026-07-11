"""
------------------------------------------------------------
File: security_service.py

Module: Authentication Services

Purpose:
Handle authentication security.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from source.modules.auth.models.login_attempt import LoginAttempt
from source.modules.auth.models.user import User
from source.modules.auth.services.email_service import EmailService


class SecurityService:
    """
    Handle authentication security.
    """

    MAX_LOGIN_ATTEMPTS = 3

    @staticmethod
    def record_login_attempt(
        *,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: str | None = None,
        user: User | None = None,
    ) -> None:
        """
        Store login attempt.
        """

        LoginAttempt.objects.create(
            user=user,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=success,
            failure_reason=reason,
        )

    @classmethod
    def record_failed_password(
        cls,
        user: User,
    ) -> None:
        """
        Increment failed login attempts.
        """

        user.failed_login_attempts += 1

        if user.failed_login_attempts >= cls.MAX_LOGIN_ATTEMPTS:

            cls.lock_account(user)

        else:

            user.save(
                update_fields=[
                    "failed_login_attempts",
                ]
            )

    @staticmethod
    def lock_account(
        user: User,
    ) -> None:
        """
        Lock user account.
        """

        user.is_locked = True

        user.save(
            update_fields=[
                "is_locked",
            ]
        )

        EmailService.send_account_locked_email(
            recipient=user.email,
        )

    @staticmethod
    def unlock_account(
        user: User,
    ) -> None:
        """
        Unlock user account.
        """

        user.is_locked = False

        user.failed_login_attempts = 0

        user.save(
            update_fields=[
                "is_locked",
                "failed_login_attempts",
            ]
        )

        EmailService.send_account_unlocked_email(
            recipient=user.email,
        )

    @staticmethod
    def reset_failed_attempts(
        user: User,
    ) -> None:
        """
        Reset failed login attempts.
        """

        user.failed_login_attempts = 0

        user.save(
            update_fields=[
                "failed_login_attempts",
            ]
        )

    @staticmethod
    def detect_suspicious_activity(
        user: User,
    ) -> bool:
        """
        Placeholder for future security analysis.
        """

        return False