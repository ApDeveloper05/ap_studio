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

from source.modules.auth.models.profile import Profile
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User
from source.modules.auth.models.otp import OTPType

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
    ) -> User:
        """
        Register a new user.
        """

        if User.objects.filter(email=email).exists():
            raise ValueError(
                "Email already registered."
            )

        with transaction.atomic():

            role = Role.objects.get(
                role_name=role_name,
            )

            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=PasswordService.hash(
                    password
                ),
                role=role,
            )

            Profile.objects.create(
                user=user,
                phone_number="",
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

            return user

    @staticmethod
    def verify_email(
        user: User,
    ) -> None:
        """
        Mark email as verified.
        """

        user.is_email_verified = True

        user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

    @staticmethod
    def resend_verification(
        user: User,
    ) -> None:
        """
        Resend verification OTP.
        """

        otp = OTPService.generate(
            user=user,
            otp_type=OTPType.EMAIL_VERIFICATION,
        )

        EmailService.send_verification_email(
            recipient=user.email,
            otp=otp.otp,
        )