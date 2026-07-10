"""
------------------------------------------------------------
File: email.py

Module: Authentication Validators

Purpose:
Validate email addresses.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import re

from source.modules.auth.models.user import User


class EmailValidator:
    """
    Handle email validation.
    """

    EMAIL_PATTERN = (
        r"^[a-zA-Z0-9._%+-]+@"
        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    @classmethod
    def validate_format(
        cls,
        email: str,
    ) -> bool:
        """
        Validate email format.
        """

        return bool(
            re.fullmatch(
                cls.EMAIL_PATTERN,
                email.strip(),
            )
        )

    @staticmethod
    def normalize(
        email: str,
    ) -> str:
        """
        Normalize email.
        """

        return email.strip().lower()

    @staticmethod
    def exists(
        email: str,
    ) -> bool:
        """
        Check whether email already exists.
        """

        return User.objects.filter(
            email=email,
        ).exists()

    @classmethod
    def validate(
        cls,
        email: str,
    ) -> tuple[bool, str]:
        """
        Validate email.
        """

        email = cls.normalize(email)

        if not email:

            return False, "Email is required."

        if not cls.validate_format(email):

            return False, "Invalid email format."

        if cls.exists(email):

            return False, "Email already registered."

        return True, ""