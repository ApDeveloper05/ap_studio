"""
------------------------------------------------------------
File: test_phase2_password_reset.py

Module: AP Studio Phase 2 Password Reset Test Suite

Purpose:
Rigorous automated testing for Phase 2 - Sprint 2.3:
Enterprise Password Reset & Recovery API Engine:
1. Forgot password OTP dispatch (POST /api/password/forgot/)
2. OTP verification & single-use JWT reset token issuance
3. Password reset execution with token & password complexity check
4. Anti-replay prevention (tokens cannot be replayed after reset)
5. Multi-device session killswitch (all active sessions terminated)
6. Password mismatch and weak password validation
7. 3-Strike brute-force defense (triggers 24h account seizure)
8. Authenticated in-session password change (POST /api/password/change/)
9. Nonexistent user handling

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-ap-studio-pwd-reset-testing",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
            "source.modules.auth",
        ],
        ROOT_URLCONF="source.modules.auth.urls",
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
        REST_FRAMEWORK={
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "source.modules.auth.api.authentication.APStudioJWTAuthentication",
            ],
        },
    )

django.setup()

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from source.modules.auth.models.otp import OTP, OTPType
from source.modules.auth.models.role import Role
from source.modules.auth.models.security import SeizedAccount
from source.modules.auth.models.session import Session
from source.modules.auth.models.user import User
from source.modules.auth.services.jwt_service import JWTService
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.session_service import SessionService


class Phase2PasswordResetEngineTests(TestCase):
    """
    Automated verification of AP Studio Password Reset & Recovery Engine.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("migrate", verbosity=0)

        cls.role_user, _ = Role.objects.get_or_create(
            role_name="user", defaults={"description": "Standard User"}
        )

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.user = User.objects.create(
            first_name="Reset",
            last_name="Tester",
            email="reset.tester@apstudio.com",
            password=PasswordService.hash("InitialPassword123!"),
            role=self.role_user,
            is_email_verified=True,
            is_active=True,
        )

    # ----------------------------------------------------------
    # Test 1: Forgot Password OTP Dispatch
    # ----------------------------------------------------------
    def test_01_forgot_password_request_otp(self):
        print("\n[PWD RESET TEST 1] Testing Forgot Password OTP Request (POST /api/password/forgot/)...")
        resp = self.client.post(
            "/api/password/forgot/",
            {"email": self.user.email},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], "PASSWORD_RESET_OTP_SENT")

        # Verify OTP record in DB
        otp_rec = OTP.objects.filter(user=self.user, otp_type=OTPType.PASSWORD_RESET).latest("created_at")
        self.assertFalse(otp_rec.is_verified)
        self.assertEqual(len(otp_rec.otp), 6)
        print(f"  ✓ Password reset OTP dispatched: {otp_rec.otp}")

    # ----------------------------------------------------------
    # Test 2: Verify Reset OTP & Issue Token
    # ----------------------------------------------------------
    def test_02_verify_reset_otp_and_issue_token(self):
        print("\n[PWD RESET TEST 2] Testing OTP Verification & Token Issuance...")
        # 1. Request OTP
        self.client.post("/api/password/forgot/", {"email": self.user.email}, format="json")
        otp_rec = OTP.objects.filter(user=self.user, otp_type=OTPType.PASSWORD_RESET).latest("created_at")

        # 2. Verify OTP
        resp = self.client.post(
            "/api/password/verify-otp/",
            {"email": self.user.email, "otp": otp_rec.otp},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], "OTP_VERIFIED")
        self.assertIn("reset_token", resp.data["data"])

        # DB marked verified
        otp_rec.refresh_from_db()
        self.assertTrue(otp_rec.is_verified)
        print("  ✓ OTP verified in DB and single-use reset_token issued.")

    # ----------------------------------------------------------
    # Test 3: Reset Password With Token & Verify New Login
    # ----------------------------------------------------------
    def test_03_reset_password_with_token(self):
        print("\n[PWD RESET TEST 3] Testing Password Reset with Token (POST /api/password/reset/)...")
        # Generate reset token
        reset_token = JWTService.generate_reset_token(user=self.user)

        new_pwd = "BrandNewSecurePassword123!"
        resp = self.client.post(
            "/api/password/reset/",
            {
                "reset_token": reset_token,
                "new_password": new_pwd,
                "confirm_password": new_pwd,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], "PASSWORD_RESET_SUCCESSFUL")

        # Verify old password fails
        self.user.refresh_from_db()
        self.assertFalse(PasswordService.verify("InitialPassword123!", self.user.password))

        # Verify new password succeeds
        self.assertTrue(PasswordService.verify(new_pwd, self.user.password))
        print("  ✓ Password successfully reset in DB and verified.")

    # ----------------------------------------------------------
    # Test 4: Anti-Replay Prevention
    # ----------------------------------------------------------
    def test_04_reset_token_anti_replay(self):
        print("\n[PWD RESET TEST 4] Testing Anti-Replay Protection on used reset tokens...")
        reset_token = JWTService.generate_reset_token(user=self.user)

        # 1st attempt -> Success
        new_pwd1 = "FirstResetPassword123!"
        resp1 = self.client.post(
            "/api/password/reset/",
            {"reset_token": reset_token, "new_password": new_pwd1, "confirm_password": new_pwd1},
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # 2nd attempt with SAME token -> Must fail!
        new_pwd2 = "SecondAttemptPassword123!"
        resp2 = self.client.post(
            "/api/password/reset/",
            {"reset_token": reset_token, "new_password": new_pwd2, "confirm_password": new_pwd2},
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp2.data["code"], "INVALID_RESET_TOKEN")
        print("  ✓ Replay attempt blocked: token invalidated by password fingerprint.")

    # ----------------------------------------------------------
    # Test 5: Multi-Device Session Killswitch
    # ----------------------------------------------------------
    def test_05_multi_device_session_killswitch(self):
        print("\n[PWD RESET TEST 5] Testing Multi-Device Session Killswitch on password reset...")
        # Simulate 3 active sessions across devices
        s1 = SessionService.create(user=self.user, ip_address="10.0.0.1", user_agent="MobileApp/1.0")
        s2 = SessionService.create(user=self.user, ip_address="10.0.0.2", user_agent="ChromeDesktop/1.0")
        s3 = SessionService.create(user=self.user, ip_address="10.0.0.3", user_agent="SafariTablet/1.0")

        self.assertEqual(Session.objects.filter(user=self.user, is_expired=False).count(), 3)

        # Execute Password Reset
        reset_token = JWTService.generate_reset_token(user=self.user)
        self.client.post(
            "/api/password/reset/",
            {
                "reset_token": reset_token,
                "new_password": "NewKilledPassword123!",
                "confirm_password": "NewKilledPassword123!",
            },
            format="json",
        )

        # Check all sessions destroyed
        active_sessions = Session.objects.filter(user=self.user, is_expired=False).count()
        self.assertEqual(active_sessions, 0)
        print("  ✓ All active sessions across devices terminated upon password reset.")

    # ----------------------------------------------------------
    # Test 6: Password Mismatch & Weak Password Validation
    # ----------------------------------------------------------
    def test_06_password_validation(self):
        print("\n[PWD RESET TEST 6] Testing Password complexity & mismatch validation...")
        reset_token = JWTService.generate_reset_token(user=self.user)

        # 1. Passwords do not match
        resp_mismatch = self.client.post(
            "/api/password/reset/",
            {
                "reset_token": reset_token,
                "new_password": "ValidPassword123!",
                "confirm_password": "DifferentPassword123!",
            },
            format="json",
        )
        self.assertEqual(resp_mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_mismatch.data["code"], "PASSWORDS_DO_NOT_MATCH")
        print("  ✓ Password mismatch caught and rejected.")

        # 2. Weak password (too short)
        resp_short = self.client.post(
            "/api/password/reset/",
            {
                "reset_token": reset_token,
                "new_password": "abc",
                "confirm_password": "abc",
            },
            format="json",
        )
        self.assertEqual(resp_short.status_code, status.HTTP_400_BAD_REQUEST)
        print("  ✓ Weak password caught and rejected.")

    # ----------------------------------------------------------
    # Test 7: 3-Strike Rule Triggers 24-Hour Account Seizure
    # ----------------------------------------------------------
    def test_07_three_strike_seizure_on_reset_otp(self):
        print("\n[PWD RESET TEST 7] Testing 3-Strike Brute-Force defense (24h Account Seizure)...")
        # Request OTP
        self.client.post("/api/password/forgot/", {"email": self.user.email}, format="json")

        # Wrong attempt 1
        resp1 = self.client.post("/api/password/verify-otp/", {"email": self.user.email, "otp": "000000"}, format="json")
        self.assertEqual(resp1.status_code, status.HTTP_400_BAD_REQUEST)

        # Wrong attempt 2
        resp2 = self.client.post("/api/password/verify-otp/", {"email": self.user.email, "otp": "000000"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

        # Wrong attempt 3 -> Triggers 24h Seizure
        resp3 = self.client.post("/api/password/verify-otp/", {"email": self.user.email, "otp": "000000"}, format="json")
        self.assertEqual(resp3.status_code, status.HTTP_423_LOCKED)
        self.assertEqual(resp3.data["code"], "ACCOUNT_SEIZED_24H")

        # Verify seizure in DB
        self.assertTrue(SeizedAccount.objects.filter(user=self.user, is_active=True).exists())
        print("  ✓ 3rd failed OTP triggered 24-hour account seizure and HTTP 423 Locked.")

    # ----------------------------------------------------------
    # Test 8: Authenticated Change Password API
    # ----------------------------------------------------------
    def test_08_authenticated_change_password(self):
        print("\n[PWD RESET TEST 8] Testing Authenticated Change Password API (POST /api/password/change/)...")
        session = SessionService.create(user=self.user, ip_address="127.0.0.1", user_agent="APIClient/1.0")
        tokens = JWTService.generate_token_pair(user=self.user, session=session)

        # 1. Invalid current password -> 400
        resp_wrong = self.client.post(
            "/api/password/change/",
            {
                "current_password": "WrongPassword123!",
                "new_password": "NewUpdatedPassword123!",
                "confirm_password": "NewUpdatedPassword123!",
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )
        self.assertEqual(resp_wrong.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_wrong.data["code"], "INVALID_CURRENT_PASSWORD")
        print("  ✓ Incorrect current password rejected.")

        # 2. Correct current password -> 200 OK
        resp_ok = self.client.post(
            "/api/password/change/",
            {
                "current_password": "InitialPassword123!",
                "new_password": "NewUpdatedPassword123!",
                "confirm_password": "NewUpdatedPassword123!",
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_ok.data["code"], "PASSWORD_CHANGED_SUCCESSFULLY")

        # Verify password in DB
        self.user.refresh_from_db()
        self.assertTrue(PasswordService.verify("NewUpdatedPassword123!", self.user.password))
        print("  ✓ Password changed successfully for authenticated user.")

    # ----------------------------------------------------------
    # Test 9: Nonexistent User Handling
    # ----------------------------------------------------------
    def test_09_forgot_password_nonexistent_user(self):
        print("\n[PWD RESET TEST 9] Testing Nonexistent User Handling...")
        resp = self.client.post(
            "/api/password/forgot/",
            {"email": "ghost.user@apstudio.com"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["code"], "USER_NOT_FOUND")
        print("  ✓ Nonexistent user correctly handled with HTTP 404.")


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(["tests.test_phase2_password_reset"])
    if failures:
        print(f"\n❌ PHASE 2 PASSWORD RESET TESTS FAILED: {failures} failures.")
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 2 PASSWORD RESET & RECOVERY TESTS PASSED 100%!")
        sys.exit(0)
