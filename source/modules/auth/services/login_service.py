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
from source.modules.auth.services.security_service import SecurityService
from source.modules.auth.services.session_service import SessionService


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
    ) -> dict:
        """
        Authenticate user.
        """

        try:

            user = User.objects.get(
                email=email,
            )

        except User.DoesNotExist:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="User not found",
            )

            return {
                "success": False,
                "code": "USER_NOT_FOUND",
                "message": "User not found.",
                "data": None,
            }

        if user.is_locked:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Account locked",
                user=user,
            )

            return {
                "success": False,
                "code": "ACCOUNT_LOCKED",
                "message": "Account is locked.",
                "data": None,
            }

        if not PasswordService.verify(
            password,
            user.password,
        ):

            SecurityService.record_failed_password(
                user,
            )

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Invalid password",
                user=user,
            )

            return {
                "success": False,
                "code": "INVALID_PASSWORD",
                "message": "Invalid password.",
                "data": None,
            }

        if not user.is_email_verified:

            SecurityService.record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Email not verified",
                user=user,
            )

            return {
                "success": False,
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Email is not verified.",
                "data": None,
            }

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

        session = SessionService.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "success": True,
            "code": "LOGIN_SUCCESS",
            "message": "Login successful.",
            "data": session,
        }

    @staticmethod
    def logout(
        session_token: str,
    ) -> dict:
        """
        Logout current user.
        """

        if SessionService.destroy(
            session_token,
        ):

            return {
                "success": True,
                "code": "LOGOUT_SUCCESS",
                "message": "Logout successful.",
                "data": None,
            }

        return {
            "success": False,
            "code": "INVALID_SESSION",
            "message": "Invalid session.",
            "data": None,
        }