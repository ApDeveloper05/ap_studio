"""
------------------------------------------------------------
File: login_service.py

Module: Authentication Services

Purpose:
Handle user authentication.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.utils import timezone

from source.modules.auth.models.user import User
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.session_service import SessionService
from source.modules.auth.services.security_service import SecurityService


class LoginService:
    """
    Handle user authentication.
    """

    @classmethod
    def login(
        cls,
        *,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
    ):
        """
        Authenticate user and create session.
        """

        try:

            user = User.objects.get(email=email)

        except User.DoesNotExist:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="User not found",
            )

            return None

        if user.is_locked:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Account locked",
                user=user,
            )

            return None

        if not PasswordService.verify(
            password,
            user.password,
        ):

            SecurityService.record_failed_password(user)

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Invalid password",
                user=user,
            )

            return None

        if not user.is_email_verified:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Email not verified",
                user=user,
            )

            return None

        user.failed_login_attempts = 0

        user.last_login = timezone.now()

        user.save(
            update_fields=[
                "failed_login_attempts",
                "last_login",
            ]
        )

        SecurityService.record_login_attempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            user=user,
        )

        return SessionService.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def logout(
        session_token: str,
    ) -> bool:
        """
        Logout current user.
        """

        return SessionService.destroy(session_token)