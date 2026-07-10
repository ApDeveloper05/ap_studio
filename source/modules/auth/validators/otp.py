"""
------------------------------------------------------------
File: otp.py

Module: Authentication Validators

Purpose:
Validate One-Time Password (OTP).

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import re


class OTPValidator:
    """
    Handle OTP validation.
    """

    OTP_LENGTH = 6

    @classmethod
    def validate(
        cls,
        otp: str,
    ) -> tuple[bool, str]:
        """
        Validate OTP.
        """

        if not otp:

            return (
                False,
                "OTP is required.",
            )

        otp = otp.strip()

        if len(otp) != cls.OTP_LENGTH:

            return (
                False,
                f"OTP must contain exactly {cls.OTP_LENGTH} digits.",
            )

        if not re.fullmatch(
            r"\d+",
            otp,
        ):

            return (
                False,
                "OTP must contain only numeric digits.",
            )

        return (
            True,
            "",
        )

    @staticmethod
    def normalize(
        otp: str,
    ) -> str:
        """
        Normalize OTP.
        """

        return otp.strip()