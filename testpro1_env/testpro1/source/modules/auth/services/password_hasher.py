"""
------------------------------------------------------------
File: password_hasher.py

Module: Authentication Services

Purpose:
Provide secure password hashing and verification utilities.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import hashlib
import hmac
import secrets

from source.core.config import settings


class PasswordHasher:
    """
    Handle password hashing operations.
    """

    @classmethod
    def generate_salt(cls) -> str:
        """
        Generate cryptographically secure salt.
        """

        return secrets.token_hex(
            settings.PASSWORD_SALT_LENGTH
        )

    @classmethod
    def hash_password(
        cls,
        password: str,
    ) -> str:
        """
        Generate password hash.
        """

        algorithm = settings.PASSWORD_HASH_ALGORITHM

        salt = cls.generate_salt()

        password_hash = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode(),
            salt=salt.encode(),
            iterations=settings.PASSWORD_HASH_ITERATIONS,
        ).hex()

        return (
            f"{algorithm}$"
            f"{settings.PASSWORD_HASH_ITERATIONS}$"
            f"{salt}$"
            f"{password_hash}"
        )

    @classmethod
    def verify_password(
        cls,
        password: str,
        stored_password: str,
    ) -> bool:
        """
        Verify password.
        """

        try:

            algorithm, iterations, salt, stored_hash = (
                stored_password.split("$")
            )

            if (
                algorithm
                != settings.PASSWORD_HASH_ALGORITHM
            ):
                return False

            generated_hash = hashlib.pbkdf2_hmac(
                hash_name="sha256",
                password=password.encode(),
                salt=salt.encode(),
                iterations=int(iterations),
            ).hex()

            return hmac.compare_digest(
                generated_hash,
                stored_hash,
            )

        except (ValueError, TypeError):

            return False