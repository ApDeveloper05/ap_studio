"""
------------------------------------------------------------
File: password_service.py

Module: Authentication Services

Purpose:
Handle password management for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.utils import timezone

from source.modules.auth.models.user import User
from source.modules.auth.services.password_hasher import PasswordHasher


class PasswordService:
    """
    Handle password operations.
    """

    @staticmethod
    def hash(
        password: str,
    ) -> str:
        """
        Generate password hash.
        """

        return PasswordHasher.hash_password(
            password,
        )

    @staticmethod
    def verify(
        password: str,
        stored_password: str,
    ) -> bool:
        """
        Verify password.
        """

        return PasswordHasher.verify_password(
            password,
            stored_password,
        )

    @classmethod
    def change_password(
        cls,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> dict:
        """
        Change user password.
        """

        if not cls.verify(
            current_password,
            user.password,
        ):

            return {
                "success": False,
                "code": "INVALID_PASSWORD",
                "message": "Current password is incorrect.",
                "data": None,
            }

        user.password = cls.hash(
            new_password,
        )

        user.password_changed_at = timezone.now()

        user.save(
            update_fields=[
                "password",
                "password_changed_at",
            ]
        )

        return {
            "success": True,
            "code": "PASSWORD_CHANGED",
            "message": "Password changed successfully.",
            "data": user,
        }

    @classmethod
    def reset_password(
        cls,
        *,
        user: User,
        new_password: str,
    ) -> dict:
        """
        Reset user password.
        """

        user.password = cls.hash(
            new_password,
        )

        user.password_changed_at = timezone.now()

        user.save(
            update_fields=[
                "password",
                "password_changed_at",
            ]
        )

        return {
            "success": True,
            "code": "PASSWORD_RESET",
            "message": "Password reset successfully.",
            "data": user,
        }