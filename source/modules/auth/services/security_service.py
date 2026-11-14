"""
------------------------------------------------------------
File: security_service.py

Module: Authentication Services

Purpose:
Enterprise security engine for AP Studio:
1. 48-Hour Hard Block on Signup (3 failed OTPs)
2. 24-Hour Global Account Seizure (3 failed OTPs on login/reset + all-device session kill)
3. Progressive Device Lockout on Failed Passwords (15 min -> 3 hours)
4. Anti-Brute-Force & Suspicious Activity Analytics

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from datetime import timedelta

from django.utils import timezone

from source.core.config import settings
from source.modules.auth.models.login_attempt import LoginAttempt
from source.modules.auth.models.security import BlockedRegistration
from source.modules.auth.models.security import SeizedAccount
from source.modules.auth.models.user import User
from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.session_service import SessionService


class SecurityService:
    """
    Enterprise Authentication Security Engine.
    """

    MAX_PASSWORD_ATTEMPTS = 5
    MAX_OTP_ATTEMPTS = 3

    SIGNUP_BLOCK_HOURS = getattr(settings, "SIGNUP_BLOCK_HOURS", 48)
    ACCOUNT_SEIZE_HOURS = getattr(settings, "ACCOUNT_SEIZE_HOURS", 24)

    DEVICE_LOCK_INITIAL_MINUTES = getattr(settings, "DEVICE_LOCKOUT_INITIAL_MINUTES", 15)
    DEVICE_LOCK_EXTENDED_HOURS = getattr(settings, "DEVICE_LOCKOUT_EXTENDED_HOURS", 3)

    # ==========================================================
    # 1. Signup Shield: 48-Hour Registration Block
    # ==========================================================

    @classmethod
    def block_registration(
        cls,
        *,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        hours: int | None = None,
    ) -> BlockedRegistration:
        """
        Hard block an email registration for 48 hours after 3 failed OTP attempts.
        Alerts both Admin and User.
        """
        block_hours = hours or cls.SIGNUP_BLOCK_HOURS
        blocked_until = timezone.now() + timedelta(hours=block_hours)

        record, _ = BlockedRegistration.objects.update_or_create(
            email=email.strip().lower(),
            defaults={
                "ip_address": ip_address,
                "user_agent": user_agent,
                "blocked_until": blocked_until,
                "reason": "3_FAILED_SIGNUP_OTP_ATTEMPTS",
                "failure_count": 3,
                "is_active": True,
            },
        )

        # Dual Alerts: User + Admin
        EmailService.send_registration_blocked_alert(
            recipient=email,
            hours=block_hours,
        )

        EmailService.send_admin_security_alert(
            title=f"Registration Blocked (48h) for {email}",
            details=(
                f"Email: {email}\n"
                f"IP Address: {ip_address}\n"
                f"User-Agent: {user_agent}\n"
                f"Blocked Until: {blocked_until}\n"
                "Reason: 3 consecutive failed OTP attempts during signup."
            ),
        )

        return record

    @classmethod
    def is_registration_blocked(
        cls,
        email: str,
    ) -> tuple[bool, BlockedRegistration | None]:
        """
        Check if email is under active 48-hour registration block.
        Returns (is_blocked: bool, record: BlockedRegistration | None).
        """
        try:
            record = BlockedRegistration.objects.get(
                email=email.strip().lower(),
                is_active=True,
            )
            if record.is_active_block:
                return True, record
            # Block expired: release
            record.is_active = False
            record.save(update_fields=["is_active"])
            return False, None
        except BlockedRegistration.DoesNotExist:
            return False, None

    # ==========================================================
    # 2. Existing User Shield: 24-Hour Account Seizure
    # ==========================================================

    @classmethod
    def seize_account(
        cls,
        *,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
        hours: int | None = None,
        reason: str = "3_FAILED_OTP_ATTEMPTS",
    ) -> SeizedAccount:
        """
        Seize/Freeze account for 24 hours.
        1. Kills all active sessions across all devices immediately.
        2. Sets is_active = False and is_email_verified = False.
        3. Creates SeizedAccount record with live countdown.
        4. Generates recovery token for automated re-verification email.
        5. Dispatches Dual Alerts (User + Admin).
        """
        seize_hours = hours or cls.ACCOUNT_SEIZE_HOURS
        seized_until = timezone.now() + timedelta(hours=seize_hours)

        # 1. Global Multi-Device Killswitch
        SessionService.destroy_all_for_user(user)

        # 2. Deactivate User Status
        user.is_active = False
        user.is_email_verified = False
        user.is_locked = True
        user.lock_until = seized_until
        user.save(update_fields=["is_active", "is_email_verified", "is_locked", "lock_until"])

        # 3. Create Seizure Record
        seizure = SeizedAccount.objects.create(
            user=user,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            seized_until=seized_until,
            reason=reason,
        )

        # 4. Generate Recovery Token
        seizure.generate_recovery_token()

        # 5. Dual Alerts: User + Admin
        EmailService.send_account_seized_alert(
            recipient=user.email,
            hours=seize_hours,
        )

        EmailService.send_admin_security_alert(
            title=f"CRITICAL: Account Frozen (24h) - {user.email}",
            details=(
                f"User Email: {user.email}\n"
                f"User ID: {user.id}\n"
                f"IP Address: {ip_address}\n"
                f"User-Agent: {user_agent}\n"
                f"Seized Until: {seized_until}\n"
                f"Reason: {reason}\n"
                "Action Taken: All active sessions destroyed across all devices."
            ),
        )

        return seizure

    @classmethod
    def is_account_seized(
        cls,
        user: User,
    ) -> tuple[bool, SeizedAccount | None]:
        """
        Check if user's account is currently under active 24-hour seizure.
        """
        try:
            seizure = SeizedAccount.objects.filter(
                user=user,
                is_recovered=False,
            ).latest("created_at")

            if seizure.is_currently_seized:
                return True, seizure
            return False, None
        except SeizedAccount.DoesNotExist:
            return False, None

    @classmethod
    def complete_account_recovery(
        cls,
        recovery_token: str,
    ) -> tuple[bool, str, User | None]:
        """
        Unfreeze and re-activate account once user completes verification.
        """
        try:
            seizure = SeizedAccount.objects.get(
                recovery_token=recovery_token,
                is_recovered=False,
            )
        except SeizedAccount.DoesNotExist:
            return False, "Invalid or expired recovery token.", None

        # Re-activate user
        user = seizure.user
        user.is_active = True
        user.is_email_verified = True
        user.is_locked = False
        user.lock_until = None
        user.failed_login_attempts = 0
        user.save(update_fields=["is_active", "is_email_verified", "is_locked", "lock_until", "failed_login_attempts"])

        # Mark seizure as recovered
        seizure.is_recovered = True
        seizure.recovered_at = timezone.now()
        seizure.save(update_fields=["is_recovered", "recovered_at"])

        EmailService.send_account_unlocked_email(recipient=user.email)

        return True, "Account successfully re-verified and unlocked.", user

    # ==========================================================
    # 3. Progressive Device Lockout (Failed Passwords)
    # ==========================================================

    @classmethod
    def is_device_locked(
        cls,
        *,
        ip_address: str,
        user_agent: str,
    ) -> tuple[bool, int, str]:
        """
        Check if THIS specific device is locked due to brute-force password guessing.
        First 5 fails -> 15 min lock.
        10+ fails -> 3 hour lock.
        Returns (is_locked: bool, remaining_seconds: int, lock_type: str).
        """
        now = timezone.now()
        three_hours_ago = now - timedelta(hours=cls.DEVICE_LOCK_EXTENDED_HOURS)

        recent_fails = LoginAttempt.objects.filter(
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=False,
            failure_reason="Invalid password",
            created_at__gte=three_hours_ago,
        ).order_by("-created_at")

        fail_count = recent_fails.count()

        if fail_count >= 10:
            latest = recent_fails.first()
            locked_until = latest.created_at + timedelta(hours=cls.DEVICE_LOCK_EXTENDED_HOURS)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds())
                return True, remaining, "3_HOURS_LOCK"

        elif fail_count >= cls.MAX_PASSWORD_ATTEMPTS:
            latest = recent_fails.first()
            locked_until = latest.created_at + timedelta(minutes=cls.DEVICE_LOCK_INITIAL_MINUTES)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds())
                return True, remaining, "15_MINUTES_LOCK"

        return False, 0, "NONE"

    # ==========================================================
    # 4. Audit & Attempt Logging
    # ==========================================================

    @staticmethod
    def record_login_attempt(
        *,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: str | None = None,
        user: User | None = None,
    ) -> None:
        """
        Store full request metadata for security analysis.
        """
        LoginAttempt.objects.create(
            user=user,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=success,
            failure_reason=reason,
        )

    @classmethod
    def record_failed_password(
        cls,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Increment failed login count on user.
        """
        user.failed_login_attempts += 1
        user.save(update_fields=["failed_login_attempts"])

    @staticmethod
    def reset_failed_attempts(
        user: User,
    ) -> None:
        """
        Reset failed login attempts on successful login.
        """
        user.failed_login_attempts = 0
        user.save(update_fields=["failed_login_attempts"])

    @staticmethod
    def detect_suspicious_activity(
        *,
        email: str,
        ip_address: str,
        user_agent: str,
    ) -> bool:
        """
        Analyze recent patterns for automated bot/crawler attacks.
        """
        five_mins_ago = timezone.now() - timedelta(minutes=5)
        rapid_fails = LoginAttempt.objects.filter(
            ip_address=ip_address,
            is_successful=False,
            created_at__gte=five_mins_ago,
        ).count()

        # More than 10 failed attempts from same IP in 5 minutes
        return rapid_fails > 10
