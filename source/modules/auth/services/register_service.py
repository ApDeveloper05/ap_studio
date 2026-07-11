"""
------------------------------------------------------------
File: register_service.py

Module: Authentication Services

Purpose:
Handle user registration workflow.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.db import transaction

from source.modules.auth.models.otp import OTPType
from source.modules.auth.models.profile import Profile
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User

from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.password_service import PasswordService


class RegisterService:
    """
    Handle user registration.
    """

    @classmethod
    def register(
        cls,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_name: str,
    ) -> dict:
        """
        Register a new user.
        """

        if User.objects.filter(email=email).exists():

            return {
                "success": False,
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email already registered.",
                "data": None,
            }

        try:

            with transaction.atomic():

                role = Role.objects.get(
                    role_name=role_name,
                )

                user = User.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=PasswordService.hash(
                        password,
                    ),
                    role=role,
                )

                Profile.objects.create(
                    user=user,
                )

                otp = OTPService.generate(
                    user=user,
                    otp_type=OTPType.EMAIL_VERIFICATION,
                )

                email_sent = (
                    EmailService.send_verification_email(
                        recipient=user.email,
                        otp=otp.otp,
                    )
                )

                if not email_sent:

                    raise RuntimeError(
                        "Verification email could not be sent."
                    )

                return {
                    "success": True,
                    "code": "REGISTRATION_SUCCESS",
                    "message": (
                        "Registration completed successfully."
                    ),
                    "data": user,
                }

        except Role.DoesNotExist:

            return {
                "success": False,
                "code": "ROLE_NOT_FOUND",
                "message": "Selected role does not exist.",
                "data": None,
            }

        except Exception:

            return {
                "success": False,
                "code": "REGISTRATION_ERROR",
                "message": (
                    "Registration failed due to an unexpected error."
                ),
                "data": None,
            }
    @staticmethod
    def verify_email(
        user: User,
    ) -> dict:
        """
        Mark user email as verified.
        """

        if user.is_email_verified:

            return {
                "success": False,
                "code": "EMAIL_ALREADY_VERIFIED",
                "message": "Email is already verified.",
                "data": None,
            }

        user.is_email_verified = True

        user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        EmailService.send_welcome_email(
            recipient=user.email,
        )

        return {
            "success": True,
            "code": "EMAIL_VERIFIED",
            "message": "Email verified successfully.",
            "data": user,
        }

    @staticmethod
    def resend_verification(
        user: User,
    ) -> dict:
        """
        Resend email verification OTP.
        """

        if user.is_email_verified:

            return {
                "success": False,
                "code": "EMAIL_ALREADY_VERIFIED",
                "message": "Email is already verified.",
                "data": None,
            }

        otp = OTPService.generate(
            user=user,
            otp_type=OTPType.EMAIL_VERIFICATION,
        )

        email_sent = (
            EmailService.send_verification_email(
                recipient=user.email,
                otp=otp.otp,
            )
        )

        if not email_sent:

            return {
                "success": False,
                "code": "EMAIL_SEND_FAILED",
                "message": "Verification email could not be sent.",
                "data": None,
            }

        return {
            "success": True,
            "code": "VERIFICATION_EMAIL_SENT",
            "message": "Verification email sent successfully.",
            "data": None,
        }