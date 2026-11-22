"""
------------------------------------------------------------
File: password_reset_service.py

Module: Authentication Services

Purpose:
Enterprise Password Reset & Recovery Service for AP Studio.
Features:
- Secure OTP dispatch with 15-minute expiration
- 3-strike brute-force defense (triggers 24h account seizure)
- Cryptographic anti-replay Single-Use Reset Token (JWT)
- Instant multi-device session killswitch upon password reset
- Authenticated in-session password change workflow

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from typing import Optional
from django.db import transaction

from source.core.logger.logger import info, warning
from source.modules.auth.models.otp import OTP, OTPType
from source.modules.auth.models.user import User
from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.jwt_service import JWTService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.security_service import SecurityService
from source.modules.auth.services.session_service import SessionService
from source.modules.auth.validators.password import PasswordValidator


class PasswordResetService:
    """
    Handles enterprise password reset, OTP verification, and password updates.
    """

    @classmethod
    def request_reset(
        cls,
        *,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Initiate password reset by dispatching a secure OTP.
        """
        user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
        if not user:
            return {
                "success": False,
                "code": "USER_NOT_FOUND",
                "message": "No active user account found with this email address.",
                "data": None,
            }

        # Check if account is under 24-hour security hold
        is_seized, seizure_rec = SecurityService.is_account_seized(user)
        if is_seized and seizure_rec:
            return {
                "success": False,
                "code": "ACCOUNT_SEIZED_24H",
                "message": (
                    f"Account is currently locked under a 24-hour security hold. "
                    f"Remaining: {seizure_rec.remaining_time_display}."
                ),
                "data": {
                    "is_seized": True,
                    "remaining": seizure_rec.remaining_time_display,
                    "recovery_token": seizure_rec.recovery_token,
                },
            }

        # Generate fresh Password Reset OTP
        otp_record = OTPService.generate(user=user, otp_type=OTPType.PASSWORD_RESET)

        # Dispatch email
        EmailService.send_password_reset_email(recipient=user.email, otp=otp_record.otp)
        info(f"[PASSWORD RESET] OTP dispatched to {user.email} (IP: {ip_address})")

        return {
            "success": True,
            "code": "PASSWORD_RESET_OTP_SENT",
            "message": "Password reset OTP sent to your registered email address.",
            "data": {"email": user.email},
        }

    @classmethod
    def verify_reset_otp(
        cls,
        *,
        email: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Verify the password reset OTP and issue a single-use password reset token.
        Enforces 3-strike rule: 3 failures trigger 24-hour account seizure.
        """
        user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
        if not user:
            return {
                "success": False,
                "code": "USER_NOT_FOUND",
                "message": "User not found.",
                "data": None,
            }

        otp_record = (
            OTP.objects.filter(user=user, otp_type=OTPType.PASSWORD_RESET, is_verified=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_record:
            return {
                "success": False,
                "code": "OTP_NOT_FOUND",
                "message": "No active password reset OTP found. Please request a new code.",
                "data": None,
            }

        is_valid, status_code = OTPService.verify(
            otp_object=otp_record,
            entered_otp=otp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not is_valid:
            if status_code == "ACCOUNT_SEIZED_24H":
                return {
                    "success": False,
                    "code": "ACCOUNT_SEIZED_24H",
                    "message": "Account seized for 24 hours due to 3 failed OTP attempts.",
                    "data": None,
                }
            return {
                "success": False,
                "code": status_code,
                "message": f"OTP verification failed: {status_code}.",
                "data": None,
            }

        # Issue single-use password reset token (valid for 15 mins)
        reset_token = JWTService.generate_reset_token(user=user, expiry_minutes=15)
        info(f"[PASSWORD RESET] OTP verified for {user.email}. Issued single-use reset token.")

        return {
            "success": True,
            "code": "OTP_VERIFIED",
            "message": "OTP verified successfully. Use the reset_token to set your new password.",
            "data": {
                "email": user.email,
                "reset_token": reset_token,
                "expires_in_minutes": 15,
            },
        }

    @classmethod
    def reset_password_with_token(
        cls,
        *,
        reset_token: str,
        new_password: str,
        confirm_password: str,
    ) -> dict:
        """
        Reset user password using the single-use JWT reset token.
        Features anti-replay verification & instant multi-device session killswitch.
        """
        # 1. Confirm passwords match
        is_match, match_err = PasswordValidator.confirm(new_password, confirm_password)
        if not is_match:
            return {
                "success": False,
                "code": "PASSWORDS_DO_NOT_MATCH",
                "message": match_err,
                "data": None,
            }

        # 2. Validate password complexity
        is_strong, strength_err = PasswordValidator.validate(new_password)
        if not is_strong:
            return {
                "success": False,
                "code": "WEAK_PASSWORD",
                "message": strength_err,
                "data": None,
            }

        # 3. Verify single-use reset token & anti-replay fingerprint
        is_valid, err_msg, user = JWTService.verify_reset_token(reset_token)
        if not is_valid or not user:
            return {
                "success": False,
                "code": "INVALID_RESET_TOKEN",
                "message": err_msg,
                "data": None,
            }

        with transaction.atomic():
            # Update password
            PasswordService.reset_password(user=user, new_password=new_password)

            # Instant Multi-Device Session Killswitch
            killed_sessions = SessionService.destroy_all_for_user(user)

        info(
            f"[PASSWORD RESET] Password successfully reset for {user.email}. "
            f"Killed {killed_sessions} active sessions across devices."
        )

        return {
            "success": True,
            "code": "PASSWORD_RESET_SUCCESSFUL",
            "message": "Password has been reset successfully. All active sessions have been terminated.",
            "data": {
                "email": user.email,
                "sessions_invalidated": killed_sessions,
            },
        }

    @classmethod
    def change_password(
        cls,
        *,
        user: User,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict:
        """
        In-session password change for authenticated users.
        """
        # 1. Verify current password
        if not PasswordService.verify(current_password, user.password):
            return {
                "success": False,
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Current password provided is incorrect.",
                "data": None,
            }

        # 2. Confirm passwords match
        is_match, match_err = PasswordValidator.confirm(new_password, confirm_password)
        if not is_match:
            return {
                "success": False,
                "code": "PASSWORDS_DO_NOT_MATCH",
                "message": match_err,
                "data": None,
            }

        # 3. Validate strength
        is_strong, strength_err = PasswordValidator.validate(new_password)
        if not is_strong:
            return {
                "success": False,
                "code": "WEAK_PASSWORD",
                "message": strength_err,
                "data": None,
            }

        with transaction.atomic():
            PasswordService.reset_password(user=user, new_password=new_password)
            # Invalidate all sessions except current? Better yet, kill all for maximum security
            killed = SessionService.destroy_all_for_user(user)

        info(f"[PASSWORD CHANGE] User {user.email} changed password. Invalidated {killed} sessions.")

        return {
            "success": True,
            "code": "PASSWORD_CHANGED_SUCCESSFULLY",
            "message": "Password changed successfully. Please log in with your new password.",
            "data": {"email": user.email},
        }
