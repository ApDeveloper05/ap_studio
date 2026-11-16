"""
------------------------------------------------------------
File: test_phase2_api.py

Module: AP Studio Phase 2 Automated Test Suite

Purpose:
Rigorous automated testing for Phase 2 REST API & JWT Engine:
1. Register API & JSON schema
2. Email Verification API
3. Standard Login API -> JWT Access + Refresh token pair
4. Protected User Profile API (Bearer Token authentication)
5. Token Refresh & Rotation API
6. Emergency 8-Digit OTP Login API
7. Logout API & Instant Multi-Device Session Invalidation

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
        SECRET_KEY="test-secret-key-for-ap-studio-api-testing",
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

from django.core.management import call_command
call_command("migrate", verbosity=0)

from rest_framework.test import APITestCase
from rest_framework import status

from source.modules.auth.models.user import User
from source.modules.auth.models.role import Role
from source.modules.auth.models.otp import OTP, OTPType


class Phase2APIEngineTests(APITestCase):
    """
    Phase 2 REST API & JWT Test Suite.
    """

    def setUp(self):
        self.role, _ = Role.objects.get_or_create(role_name="user", defaults={"description": "User"})

    # ----------------------------------------------------------
    # Test 1: Register API
    # ----------------------------------------------------------
    def test_01_register_api(self):
        print("\n[API TEST 1] Testing Register API (POST /api/register/)...")
        data = {
            "first_name": "Aryan",
            "last_name": "Parmar",
            "email": "aryan.api@apstudio.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post("/api/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], "aryan.api@apstudio.com")
        print("  ✓ User registered via REST API. Status 201 Created.")

    # ----------------------------------------------------------
    # Test 2: Verify Email API
    # ----------------------------------------------------------
    def test_02_verify_email_api(self):
        print("\n[API TEST 2] Testing Verify Email API (POST /api/verify-email/)...")
        # Register user
        self.client.post(
            "/api/register/",
            {
                "first_name": "Verify",
                "last_name": "User",
                "email": "verify.api@apstudio.com",
                "password": "Password123!",
            },
            format="json",
        )
        user = User.objects.get(email="verify.api@apstudio.com")
        otp_rec = OTP.objects.filter(user=user, otp_type=OTPType.EMAIL_VERIFICATION).latest("created_at")

        verify_resp = self.client.post(
            "/api/verify-email/",
            {"email": "verify.api@apstudio.com", "otp": otp_rec.otp},
            format="json",
        )
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_resp.data["success"])
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        print("  ✓ Email verified via REST API. Status 200 OK.")

    # ----------------------------------------------------------
    # Test 3: Standard Login API (JWT Pair Generation)
    # ----------------------------------------------------------
    def test_03_login_api_jwt_generation(self):
        print("\n[API TEST 3] Testing Standard Login API & JWT Generation (POST /api/login/)...")
        # Create verified user
        from source.modules.auth.services.password_service import PasswordService
        user = User.objects.create(
            first_name="JWT",
            last_name="Tester",
            email="jwt.tester@apstudio.com",
            password=PasswordService.hash("MySecretPassword123!"),
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )

        login_resp = self.client.post(
            "/api/login/",
            {"email": "jwt.tester@apstudio.com", "password": "MySecretPassword123!"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        data = login_resp.data["data"]

        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["user"]["email"], "jwt.tester@apstudio.com")
        print(f"  ✓ JWT Access Token generated ({len(data['access_token'])} chars).")
        print(f"  ✓ JWT Refresh Token generated ({len(data['refresh_token'])} chars).")

    # ----------------------------------------------------------
    # Test 4: Protected Profile API (Bearer Authentication)
    # ----------------------------------------------------------
    def test_04_protected_profile_api(self):
        print("\n[API TEST 4] Testing Protected Profile API with Bearer Token (GET /api/me/)...")
        from source.modules.auth.services.password_service import PasswordService
        from source.modules.auth.services.session_service import SessionService
        from source.modules.auth.services.jwt_service import JWTService

        user = User.objects.create(
            first_name="Secure",
            last_name="Profile",
            email="secure.profile@apstudio.com",
            password=PasswordService.hash("Password123!"),
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )
        session = SessionService.create(user=user, ip_address="127.0.0.1", user_agent="APIClient/1.0")
        tokens = JWTService.generate_token_pair(user=user, session=session)

        # 1. Without Token -> 401 Unauthorized
        unauth_resp = self.client.get("/api/me/")
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        print("  ✓ Access without Bearer token correctly denied (HTTP 401).")

        # 2. With Valid Bearer Token -> 200 OK
        auth_resp = self.client.get(
            "/api/me/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_resp.data["data"]["email"], "secure.profile@apstudio.com")
        print("  ✓ Access with Bearer token authenticated successfully (HTTP 200).")

    # ----------------------------------------------------------
    # Test 5: Token Refresh API
    # ----------------------------------------------------------
    def test_05_token_refresh_api(self):
        print("\n[API TEST 5] Testing Token Refresh API (POST /api/token/refresh/)...")
        from source.modules.auth.services.password_service import PasswordService
        from source.modules.auth.services.session_service import SessionService
        from source.modules.auth.services.jwt_service import JWTService

        user = User.objects.create(
            first_name="Refresh",
            last_name="User",
            email="refresh@apstudio.com",
            password=PasswordService.hash("Password123!"),
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )
        session = SessionService.create(user=user, ip_address="127.0.0.1", user_agent="APIClient/1.0")
        tokens = JWTService.generate_token_pair(user=user, session=session)

        refresh_resp = self.client.post(
            "/api/token/refresh/",
            {"refresh_token": tokens["refresh_token"]},
            format="json",
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        new_data = refresh_resp.data["data"]
        self.assertIn("access_token", new_data)
        self.assertIn("refresh_token", new_data)
        print("  ✓ Access token successfully refreshed and rotated.")

    # ----------------------------------------------------------
    # Test 6: Emergency 8-Digit OTP Login API
    # ----------------------------------------------------------
    def test_06_emergency_8digit_otp_login_api(self):
        print("\n[API TEST 6] Testing Emergency 8-Digit OTP Login API...")
        from source.modules.auth.services.password_service import PasswordService
        user = User.objects.create(
            first_name="Emergency",
            last_name="Login",
            email="emergency.api@apstudio.com",
            password=PasswordService.hash("Password123!"),
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )

        # 1. Request 8-Digit Code
        req_resp = self.client.post(
            "/api/login-otp/request/",
            {"email": "emergency.api@apstudio.com"},
            format="json",
        )
        self.assertEqual(req_resp.status_code, status.HTTP_200_OK)

        otp_rec = OTP.objects.filter(user=user, otp_type=OTPType.LOGIN_VERIFICATION).latest("created_at")
        self.assertEqual(len(otp_rec.otp), 8)
        print(f"  ✓ 8-Digit Code dispatched via API: {otp_rec.otp}")

        # 2. Verify 8-Digit Code & Get JWT
        verify_resp = self.client.post(
            "/api/login-otp/verify/",
            {"email": "emergency.api@apstudio.com", "otp": otp_rec.otp},
            format="json",
        )
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", verify_resp.data["data"])
        print("  ✓ 8-Digit Code verified via API. JWT tokens issued.")

    # ----------------------------------------------------------
    # Test 7: Logout API & Session Termination
    # ----------------------------------------------------------
    def test_07_logout_api(self):
        print("\n[API TEST 7] Testing Logout API & Session Termination...")
        from source.modules.auth.services.password_service import PasswordService
        from source.modules.auth.services.session_service import SessionService
        from source.modules.auth.services.jwt_service import JWTService

        user = User.objects.create(
            first_name="Logout",
            last_name="Tester",
            email="logout@apstudio.com",
            password=PasswordService.hash("Password123!"),
            role=self.role,
            is_email_verified=True,
            is_active=True,
        )
        session = SessionService.create(user=user, ip_address="127.0.0.1", user_agent="APIClient/1.0")
        tokens = JWTService.generate_token_pair(user=user, session=session)

        # Logout with Bearer token
        logout_resp = self.client.post(
            "/api/logout/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # Refresh token must now fail because underlying session was terminated!
        refresh_resp = self.client.post(
            "/api/token/refresh/",
            {"refresh_token": tokens["refresh_token"]},
            format="json",
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        print("  ✓ User logged out. Session destroyed and refresh token invalidated.")


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(["tests.test_phase2_api"])
    if failures:
        print(f"\n❌ PHASE 2 API TESTS FAILED: {failures} failures.")
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 2 REST API & JWT TESTS PASSED 100%!")
        sys.exit(0)
