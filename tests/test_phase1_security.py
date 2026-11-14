"""
------------------------------------------------------------
File: test_phase1_security.py

Module: AP Studio Phase 1 Automated Test Suite

Purpose:
Rigorous automated tests for Phase 1 Authentication & Security Engine:
1. User registration & Role creation
2. 8-Digit Emergency Login OTP
3. 48-Hour Registration Block on 3 failed OTPs
4. 24-Hour Account Seizure on 3 failed login/reset OTPs
5. Multi-device Session Killswitch
6. Progressive Device Lockout (15m -> 3h)
7. Post-Freeze Automated Recovery flow

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import os
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
from django.conf import settings

# In-memory test settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-ap-studio-testing",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "source.modules.auth",
        ],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST_USER="testing@apstudio.com",
        TIME_ZONE="UTC",
        USE_TZ=True,
        OTP_LENGTH=6,
        LOGIN_OTP_LENGTH=8,
        OTP_EXPIRY_MINUTES=15,
        OTP_MAX_RETRY=3,
        SIGNUP_BLOCK_HOURS=48,
        ACCOUNT_SEIZE_HOURS=24,
        DEVICE_LOCKOUT_INITIAL_MINUTES=15,
        DEVICE_LOCKOUT_EXTENDED_HOURS=3,
    )

django.setup()

# Create tables in memory
from django.core.management import call_command
call_command("migrate", verbosity=0)

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from source.modules.auth.models.user import User
from source.modules.auth.models.role import Role
from source.modules.auth.models.otp import OTP, OTPType
from source.modules.auth.models.session import Session
from source.modules.auth.models.security import BlockedRegistration, SeizedAccount
from source.modules.auth.services.register_service import RegisterService
from source.modules.auth.services.login_service import LoginService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.security_service import SecurityService
from source.modules.auth.services.session_service import SessionService


class Phase1SecurityEngineTests(TestCase):
    """
    Complete Phase 1 Validation Suite.
    """

    def setUp(self):
        # Ensure default role exists
        self.role, _ = Role.objects.get_or_create(role_name="user", defaults={"description": "User"})

    # ----------------------------------------------------------
    # Test 1: User Registration
    # ----------------------------------------------------------
    def test_01_user_registration(self):
        print("\n[TEST 1] Testing User Registration...")
        resp = RegisterService.register(
            first_name="Aryan",
            last_name="Parmar",
            email="aryan.test1@apstudio.com",
            password="StrongPassword123!",
        )
        self.assertTrue(resp["success"], f"Registration failed: {resp.get('message')}")
        self.assertEqual(resp["code"], "REGISTRATION_SUCCESS")
        user = User.objects.get(email="aryan.test1@apstudio.com")
        self.assertFalse(user.is_email_verified)
        print("  ✓ User registered with unverified status.")

    # ----------------------------------------------------------
    # Test 2: 8-Digit Emergency Login OTP
    # ----------------------------------------------------------
    def test_02_eight_digit_login_otp(self):
        print("\n[TEST 2] Testing 8-Digit Emergency Login OTP...")
        # Create verified user
        user = User.objects.create(
            first_name="Test",
            last_name="User",
            email="emergency@apstudio.com",
            password="hash",
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )

        req_resp = LoginService.request_login_otp(
            email="emergency@apstudio.com",
            ip_address="127.0.0.1",
            user_agent="TestBrowser/1.0",
        )
        self.assertTrue(req_resp["success"])
        self.assertEqual(req_resp["code"], "LOGIN_OTP_DISPATCHED")

        # Verify OTP in DB is exactly 8 digits
        otp_rec = OTP.objects.filter(user=user, otp_type=OTPType.LOGIN_VERIFICATION).latest("created_at")
        self.assertEqual(len(otp_rec.otp), 8, f"Expected 8 digits, got: {otp_rec.otp}")
        self.assertTrue(otp_rec.otp.isdigit())
        print(f"  ✓ 8-Digit Code generated: {otp_rec.otp}")

        # Verify correct OTP
        verify_resp = LoginService.verify_login_otp(
            email="emergency@apstudio.com",
            entered_otp=otp_rec.otp,
            ip_address="127.0.0.1",
            user_agent="TestBrowser/1.0",
        )
        self.assertTrue(verify_resp["success"])
        self.assertEqual(verify_resp["code"], "LOGIN_SUCCESS")
        self.assertIsNotNone(verify_resp["data"].session_token)
        print("  ✓ 8-Digit Code successfully authenticated and established session.")

    # ----------------------------------------------------------
    # Test 3: 48-Hour Hard Block on Signup (3 Failed OTPs)
    # ----------------------------------------------------------
    def test_03_forty_eight_hour_signup_block(self):
        print("\n[TEST 3] Testing 48-Hour Hard Block on 3 Failed Signup OTPs...")
        reg_resp = RegisterService.register(
            first_name="Attacker",
            last_name="Bot",
            email="target@botattack.com",
            password="Password123!",
        )
        user = reg_resp["data"]

        # Fail 1
        resp1 = RegisterService.verify_email(user=user, entered_otp="000000", ip_address="1.2.3.4")
        self.assertFalse(resp1["success"])

        # Fail 2
        resp2 = RegisterService.verify_email(user=user, entered_otp="111111", ip_address="1.2.3.4")
        self.assertFalse(resp2["success"])

        # Fail 3 (Should trigger 48-hour hard block!)
        resp3 = RegisterService.verify_email(user=user, entered_otp="222222", ip_address="1.2.3.4")
        self.assertFalse(resp3["success"])
        self.assertEqual(resp3["code"], "REGISTRATION_BLOCKED_48H")
        print("  ✓ 3rd failure triggered 48-Hour Hard Block.")

        # Check DB Block Record
        is_blocked, block_rec = SecurityService.is_registration_blocked("target@botattack.com")
        self.assertTrue(is_blocked)
        self.assertGreater(block_rec.remaining_seconds, 47 * 3600)
        print(f"  ✓ Database Block active. Remaining: {block_rec.remaining_formatted}")

        # Re-registration attempt must be strictly blocked
        re_reg = RegisterService.register(
            first_name="Attacker",
            last_name="Bot",
            email="target@botattack.com",
            password="Password123!",
        )
        self.assertFalse(re_reg["success"])
        self.assertEqual(re_reg["code"], "REGISTRATION_BLOCKED_48H")
        print("  ✓ Re-registration with blocked email rejected immediately.")

    # ----------------------------------------------------------
    # Test 4: 24-Hour Account Seizure & Global Session Kill
    # ----------------------------------------------------------
    def test_04_twenty_four_hour_account_seizure_and_session_kill(self):
        print("\n[TEST 4] Testing 24-Hour Account Seizure & Multi-Device Session Kill...")
        user = User.objects.create(
            first_name="Victim",
            last_name="Account",
            email="victim@apstudio.com",
            password="hash",
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )

        # Create 3 active sessions across different devices (Phone, Tablet, Laptop)
        s1 = SessionService.create(user=user, ip_address="10.0.0.1", user_agent="Phone")
        s2 = SessionService.create(user=user, ip_address="10.0.0.2", user_agent="Tablet")
        s3 = SessionService.create(user=user, ip_address="10.0.0.3", user_agent="Laptop")

        self.assertEqual(Session.objects.filter(user=user, is_expired=False).count(), 3)
        print("  ✓ 3 active sessions simulated across devices.")

        # Request Login OTP
        LoginService.request_login_otp(email="victim@apstudio.com", ip_address="1.1.1.1", user_agent="Attacker")

        # 3 Failed OTP attempts on victim's account
        LoginService.verify_login_otp(email="victim@apstudio.com", entered_otp="00000000", ip_address="1.1.1.1", user_agent="Attacker")
        LoginService.verify_login_otp(email="victim@apstudio.com", entered_otp="11111111", ip_address="1.1.1.1", user_agent="Attacker")
        final_fail = LoginService.verify_login_otp(email="victim@apstudio.com", entered_otp="22222222", ip_address="1.1.1.1", user_agent="Attacker")

        self.assertFalse(final_fail["success"])
        self.assertEqual(final_fail["code"], "ACCOUNT_SEIZED_24H")
        print("  ✓ 3rd failure triggered 24-Hour Account Seizure.")

        # Verify User status is deactivated
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.is_locked)

        # Verify all sessions were instantly killed
        active_sessions = Session.objects.filter(user=user, is_expired=False).count()
        self.assertEqual(active_sessions, 0)
        print("  ✓ Multi-Device Session Killswitch SUCCESS: All 3 active sessions destroyed.")

        # Verify SeizedAccount record exists
        is_seized, seizure = SecurityService.is_account_seized(user)
        self.assertTrue(is_seized)
        self.assertIsNotNone(seizure.recovery_token)
        print(f"  ✓ Seizure confirmed in DB. Recovery Token: {seizure.recovery_token[:12]}...")

    # ----------------------------------------------------------
    # Test 5: Progressive Device Lockout
    # ----------------------------------------------------------
    def test_05_progressive_device_lockout(self):
        print("\n[TEST 5] Testing Progressive Device Lockout (5 Fails -> 15m Lock)...")
        test_ip = "192.168.1.100"
        test_agent = "BadHackerBot/2.0"

        # Record 5 failed password attempts from this device
        for i in range(5):
            SecurityService.record_login_attempt(
                email="anyone@apstudio.com",
                ip_address=test_ip,
                user_agent=test_agent,
                success=False,
                reason="Invalid password",
            )

        is_locked, remaining, lock_type = SecurityService.is_device_locked(
            ip_address=test_ip,
            user_agent=test_agent,
        )
        self.assertTrue(is_locked)
        self.assertEqual(lock_type, "15_MINUTES_LOCK")
        self.assertGreater(remaining, 14 * 60)
        print(f"  ✓ Device {test_ip} successfully locked for 15 minutes ({remaining}s remaining).")

        # Innocent device from another IP should NOT be locked!
        innocent_locked, _, _ = SecurityService.is_device_locked(
            ip_address="192.168.1.200",
            user_agent="LegitUser/1.0",
        )
        self.assertFalse(innocent_locked)
        print("  ✓ Innocent user from different IP remains unaffected.")

    # ----------------------------------------------------------
    # Test 6: Post-Freeze Automated Recovery Flow
    # ----------------------------------------------------------
    def test_06_post_freeze_account_recovery(self):
        print("\n[TEST 6] Testing Automated Account Recovery & Re-Activation...")
        user = User.objects.create(
            first_name="Restored",
            last_name="User",
            email="restore@apstudio.com",
            password="hash",
            role=self.role,
            is_email_verified=False,
            is_active=False,
            is_locked=True,
        )

        seizure = SeizedAccount.objects.create(
            user=user,
            email=user.email,
            seized_until=timezone.now() - timedelta(minutes=1), # Expired freeze
            reason="3_FAILED_OTP_ATTEMPTS",
        )
        token = seizure.generate_recovery_token()

        ok, msg, restored_user = SecurityService.complete_account_recovery(recovery_token=token)
        self.assertTrue(ok)
        self.assertTrue(restored_user.is_active)
        self.assertTrue(restored_user.is_email_verified)
        self.assertFalse(restored_user.is_locked)
        print("  ✓ User successfully restored to full active and verified status.")


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(["tests.test_phase1_security"])
    if failures:
        print(f"\n❌ TESTS FAILED: {failures} failures.")
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 1 SECURITY & AUTH TESTS PASSED 100%!")
        sys.exit(0)
