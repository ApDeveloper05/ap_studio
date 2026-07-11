"""
------------------------------------------------------------
File: password.py

Module: Authentication Validators

Purpose:
Validate user passwords.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import re


class PasswordValidator:
    """
    Handle password validation.
    """

    MIN_LENGTH = 8

    SPECIAL_CHARACTERS = "@$!%*?&#"

    @classmethod
    def validate(
        cls,
        password: str,
    ) -> tuple[bool, str]:
        """
        Validate password strength.
        """

        if not password:

            return False, "Password is required."

        if len(password) < cls.MIN_LENGTH:

            return (
                False,
                f"Password must contain at least {cls.MIN_LENGTH} characters.",
            )

        if not re.search(r"[A-Z]", password):

            return (
                False,
                "Password must contain at least one uppercase letter.",
            )

        if not re.search(r"[a-z]", password):

            return (
                False,
                "Password must contain at least one lowercase letter.",
            )

        if not re.search(r"\d", password):

            return (
                False,
                "Password must contain at least one digit.",
            )

        if not re.search(
            f"[{re.escape(cls.SPECIAL_CHARACTERS)}]",
            password,
        ):

            return (
                False,
                "Password must contain at least one special character.",
            )

        return True, ""

    @staticmethod
    def confirm(
        password: str,
        confirm_password: str,
    ) -> tuple[bool, str]:
        """
        Validate password confirmation.
        """

        if password != confirm_password:

            return (
                False,
                "Passwords do not match.",
            )

        return True, ""