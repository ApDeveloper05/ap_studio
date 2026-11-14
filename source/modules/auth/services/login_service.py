"""
------------------------------------------------------------
File: login_service.py

Module: Authentication Services

Purpose:
Handle user authentication with:
1. Standard Password Login + Progressive Device Lockout (15m -> 3h)
2. Emergency 8-Digit OTP Login (Passwordless)
3. 24-Hour Account Seizure enforcement & session management

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.utils import timezone

from source.modules.auth.models.otp import OTP
from source.modules.auth.models.otp import OTPType
from source.modules.auth.models.user import User

from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.security_service import SecurityService
from source.modules.auth.services.session_service import SessionService


class LoginService:
    """
    Handle user authentication with enterprise security safeguards.
    """

    # ==========================================================
    # 1. Standard Password Authentication
    # ==========================================================

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
        Authenticate user with device lockout & account seizure checks.
        """
        normalized_email = email.strip().lower()

        # 1. Device-Specific Progressive Lockout Check
        is_dev_locked, remaining_secs, lock_type = SecurityService.is_device_locked(
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if is_dev_locked:
            minutes = max(1, remaining_secs // 60)
            return {
                "success": False,
                "code": "DEVICE_LOCKED",
                "message": (
                    f"This device is temporarily locked due to multiple failed password attempts. "
                    f"Please try again in {minutes} minute(s)."
                ),
                "data": {"remaining_seconds": remaining_secs, "lock_type": lock_type},
            }

        # 2. User Lookup
        try:
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist:
            SecurityService.record_login_attempt(
                email=normalized_email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="User not found",
            )
            return {
                "success": False,
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "data": None,
            }

        # 3. Account Seizure (24-Hour Freeze Check)
        is_seized, seizure_record = SecurityService.is_account_seized(user)
        if is_seized and seizure_record:
            return {
                "success": False,
                "code": "ACCOUNT_SEIZED_24H",
                "message": (
                    f"Account is currently FROZEN for security reasons. "
                    f"Remaining time: {seizure_record.remaining_formatted}. "
                    "Check your email for the automated recovery link."
                ),
                "data": {
                    "remaining_seconds": seizure_record.remaining_seconds,
                    "remaining_formatted": seizure_record.remaining_formatted,
                },
            }

        # 4. Standard Account Lock Check
        if user.is_locked:
            return {
                "success": False,
                "code": "ACCOUNT_LOCKED",
                "message": "Account is locked. Please contact support or use account recovery.",
                "data": None,
            }

        # 5. Password Verification
        if not PasswordService.verify(password, user.password):
            SecurityService.record_failed_password(user, ip_address=ip_address, user_agent=user_agent)
            SecurityService.record_login_attempt(
                email=normalized_email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Invalid password",
                user=user,
            )

            # Check if this failure just triggered a device lock
            now_locked, lock_secs, _ = SecurityService.is_device_locked(
                ip_address=ip_address,
                user_agent=user_agent,
            )
            if now_locked:
                return {
                    "success": False,
                    "code": "DEVICE_LOCKED",
                    "message": (
                        f"5 failed attempts! This device is locked for {max(1, lock_secs // 60)} minute(s)."
                    ),
                    "data": {"remaining_seconds": lock_secs},
                }

            return {
                "success": False,
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "data": None,
            }

        # 6. Email Verification Check
        if not user.is_email_verified:
            SecurityService.record_login_attempt(
                email=normalized_email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason="Email not verified",
                user=user,
            )
            return {
                "success": False,
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Email is not verified. Please verify your email OTP before logging in.",
                "data": {"user_id": str(user.id)},
            }

        # 7. Success - Establish Session
        SecurityService.reset_failed_attempts(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        SecurityService.record_login_attempt(
            email=normalized_email,
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

    # ==========================================================
    # 2. Emergency 8-Digit OTP Login (Passwordless)
    # ==========================================================

    @classmethod
    def request_login_otp(
        cls,
        *,
        email: str,
        ip_address: str,
        user_agent: str,
    ) -> dict:
        """
        Generate and dispatch an 8-Digit cryptographic OTP for emergency login.
        """
        normalized_email = email.strip().lower()

        try:
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist:
            # Generic response for anti-enumeration
            return {
                "success": True,
                "code": "LOGIN_OTP_DISPATCHED",
                "message": "If an account exists with this email, an 8-digit security code has been sent.",
                "data": None,
            }

        # Check account seizure
        is_seized, seizure = SecurityService.is_account_seized(user)
        if is_seized and seizure:
            return {
                "success": False,
                "code": "ACCOUNT_SEIZED_24H",
                "message": (
                    f"Account is currently FROZEN. Remaining time: {seizure.remaining_formatted}."
                ),
                "data": {"remaining_seconds": seizure.remaining_seconds},
            }

        # Generate 8-Digit OTP
        otp_record = OTPService.generate(
            user=user,
            otp_type=OTPType.LOGIN_VERIFICATION,
            length=8,
        )

        EmailService.send_login_otp_email(
            recipient=user.email,
            otp=otp_record.otp,
        )

        return {
            "success": True,
            "code": "LOGIN_OTP_DISPATCHED",
            "message": "An 8-digit emergency login code has been sent to your email.",
            "data": {"user_id": str(user.id)},
        }

    @classmethod
    def verify_login_otp(
        cls,
        *,
        email: str,
        entered_otp: str,
        ip_address: str,
        user_agent: str,
    ) -> dict:
        """
        Verify the 8-Digit Login OTP.
        3 failed attempts trigger 24-hour account freeze and kill all sessions!
        """
        normalized_email = email.strip().lower()

        try:
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist:
            return {
                "success": False,
                "code": "INVALID_OTP",
                "message": "Invalid verification code.",
                "data": None,
            }

        # Check existing seizure
        is_seized, seizure = SecurityService.is_account_seized(user)
        if is_seized and seizure:
            return {
                "success": False,
                "code": "ACCOUNT_SEIZED_24H",
                "message": f"Account is FROZEN. Remaining time: {seizure.remaining_formatted}.",
                "data": {"remaining_seconds": seizure.remaining_seconds},
            }

        # Fetch active 8-digit login OTP
        otp_record = OTP.objects.filter(
            user=user,
            otp_type=OTPType.LOGIN_VERIFICATION,
            is_verified=False,
        ).order_by("-created_at").first()

        if not otp_record:
            return {
                "success": False,
                "code": "OTP_NOT_FOUND",
                "message": "No active login code found. Please request a new one.",
                "data": None,
            }

        success, status_code = OTPService.verify(
            otp_object=otp_record,
            entered_otp=entered_otp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not success:
            if status_code == "ACCOUNT_SEIZED_24H":
                return {
                    "success": False,
                    "code": "ACCOUNT_SEIZED_24H",
                    "message": (
                        "CRITICAL: 3 failed OTP attempts detected! Your account has been FROZEN "
                        "for 24 hours and all active sessions across all devices have been terminated."
                    ),
                    "data": None,
                }

            remaining = otp_record.maximum_retry - otp_record.retry_count
            return {
                "success": False,
                "code": status_code,
                "message": f"Invalid 8-digit code. {remaining} attempt(s) remaining.",
                "data": {"remaining_attempts": remaining},
            }

        # Success - Establish Session & Re-activate if needed
        user.is_email_verified = True
        user.is_active = True
        user.failed_login_attempts = 0
        user.last_login = timezone.now()
        user.save(update_fields=["is_email_verified", "is_active", "failed_login_attempts", "last_login"])

        session = SessionService.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        SecurityService.record_login_attempt(
            email=normalized_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            user=user,
        )

        return {
            "success": True,
            "code": "LOGIN_SUCCESS",
            "message": "Login verified successfully via 8-digit security code.",
            "data": session,
        }

    # ==========================================================
    # 3. Session Termination (Logout)
    # ==========================================================

    @staticmethod
    def logout(
        session_token: str,
    ) -> dict:
        """
        Logout current session.
        """
        if SessionService.destroy(session_token):
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
