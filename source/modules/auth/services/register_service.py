"""
------------------------------------------------------------
File: register_service.py

Module: Authentication Services

Purpose:
Handle user registration workflow with 48-hour security block check
and OTP verification engine.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.db import transaction

from source.modules.auth.models.otp import OTP
from source.modules.auth.models.otp import OTPType
from source.modules.auth.models.profile import Profile
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User

from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.security_service import SecurityService


class RegisterService:
    """
    Handle user registration and email verification.
    """

    @classmethod
    def register(
        cls,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Register a new user after verifying 48h security block status.
        """
        normalized_email = email.strip().lower()

        # 1. 48-Hour Hard Block Check
        is_blocked, block_record = SecurityService.is_registration_blocked(normalized_email)
        if is_blocked and block_record:
            return {
                "success": False,
                "code": "REGISTRATION_BLOCKED_48H",
                "message": (
                    f"Registration for this email is locked for another {block_record.remaining_formatted} "
                    "due to 3 failed OTP attempts."
                ),
                "data": {
                    "remaining_seconds": block_record.remaining_seconds,
                    "remaining_formatted": block_record.remaining_formatted,
                },
            }

        # 2. Duplicate Check
        if User.objects.filter(email=normalized_email).exists():
            return {
                "success": False,
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email already registered.",
                "data": None,
            }

        try:
            with transaction.atomic():
                role, _ = Role.objects.get_or_create(
                    role_name="user",
                    defaults={"description": "Standard User"},
                )

                user = User.objects.create(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    email=normalized_email,
                    password=PasswordService.hash(password),
                    role=role,
                    is_email_verified=False,
                )

                Profile.objects.create(user=user)

                otp = OTPService.generate(
                    user=user,
                    otp_type=OTPType.EMAIL_VERIFICATION,
                )

                email_sent = EmailService.send_verification_email(
                    recipient=user.email,
                    otp=otp.otp,
                )

                if not email_sent:
                    raise RuntimeError("Verification email could not be sent.")

                return {
                    "success": True,
                    "code": "REGISTRATION_SUCCESS",
                    "message": "Registration completed successfully. Please verify your OTP.",
                    "data": user,
                }

        except Exception as e:
            return {
                "success": False,
                "code": "REGISTRATION_ERROR",
                "message": f"Registration failed: {str(e)}",
                "data": None,
            }

    @classmethod
    def verify_email(
        cls,
        *,
        user: User,
        entered_otp: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Verify user email OTP with 3-attempt 48-hour block protection.
        """
        if user.is_email_verified:
            return {
                "success": False,
                "code": "EMAIL_ALREADY_VERIFIED",
                "message": "Email is already verified.",
                "data": user,
            }

        # Check 48h block
        is_blocked, block_record = SecurityService.is_registration_blocked(user.email)
        if is_blocked and block_record:
            return {
                "success": False,
                "code": "REGISTRATION_BLOCKED_48H",
                "message": (
                    f"Account registration is locked for another {block_record.remaining_formatted} "
                    "due to 3 failed OTP attempts."
                ),
                "data": {
                    "remaining_seconds": block_record.remaining_seconds,
                    "remaining_formatted": block_record.remaining_formatted,
                },
            }

        # Fetch active OTP
        otp_record = OTP.objects.filter(
            user=user,
            otp_type=OTPType.EMAIL_VERIFICATION,
            is_verified=False,
        ).order_by("-created_at").first()

        if not otp_record:
            return {
                "success": False,
                "code": "OTP_NOT_FOUND",
                "message": "No active verification OTP found. Please request a new one.",
                "data": None,
            }

        success, status_code = OTPService.verify(
            otp_object=otp_record,
            entered_otp=entered_otp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not success:
            if status_code == "REGISTRATION_BLOCKED_48H":
                return {
                    "success": False,
                    "code": "REGISTRATION_BLOCKED_48H",
                    "message": (
                        "3 failed attempts detected! Your email registration has been locked "
                        "for 48 hours for security reasons."
                    ),
                    "data": None,
                }

            remaining = otp_record.maximum_retry - otp_record.retry_count
            return {
                "success": False,
                "code": status_code,
                "message": f"Invalid OTP code. You have {remaining} attempt(s) remaining.",
                "data": {"remaining_attempts": remaining},
            }

        # Success - Activate User
        user.is_email_verified = True
        user.is_active = True
        user.save(update_fields=["is_email_verified", "is_active"])

        EmailService.send_welcome_email(recipient=user.email)

        return {
            "success": True,
            "code": "EMAIL_VERIFIED",
            "message": "Email verified successfully! You can now log in.",
            "data": user,
        }

    @classmethod
    def resend_verification(
        cls,
        user: User,
    ) -> dict:
        """
        Resend email verification OTP with 48h block check.
        """
        if user.is_email_verified:
            return {
                "success": False,
                "code": "EMAIL_ALREADY_VERIFIED",
                "message": "Email is already verified.",
                "data": None,
            }

        is_blocked, block_record = SecurityService.is_registration_blocked(user.email)
        if is_blocked and block_record:
            return {
                "success": False,
                "code": "REGISTRATION_BLOCKED_48H",
                "message": (
                    f"Cannot resend OTP. Registration is locked for another {block_record.remaining_formatted}."
                ),
                "data": {"remaining_seconds": block_record.remaining_seconds},
            }

        otp = OTPService.generate(
            user=user,
            otp_type=OTPType.EMAIL_VERIFICATION,
        )

        email_sent = EmailService.send_verification_email(
            recipient=user.email,
            otp=otp.otp,
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
            "message": "A fresh verification OTP has been sent to your email.",
            "data": None,
        }
