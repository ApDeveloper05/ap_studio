"""
------------------------------------------------------------
File: test_phase2_docs_throttling.py

Module: AP Studio Phase 2 Documentation & Rate Limiting Test Suite

Purpose:
Rigorous automated testing for Phase 2 - Sprint 2.4:
OpenAPI 3.0.3 Schema, Swagger UI, ReDoc, and API Throttling:
1. OpenAPI 3.0.3 Schema generation (GET /api/schema/)
2. Interactive Swagger UI rendering (GET /api/docs/)
3. ReDoc reference documentation rendering (GET /api/redoc/)
4. Login Burst Rate Limiting (HTTP 429 Too Many Requests)
5. Password Reset Rate Limiting (HTTP 429 Too Many Requests)
6. Registration Rate Limiting (HTTP 429 Too Many Requests)
7. Client IP Isolation in Throttling

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
        SECRET_KEY="test-secret-key-for-ap-studio-docs-throttling",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "aps_throttle_test_cache",
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
            "DEFAULT_THROTTLE_RATES": {
                "anon": "100/minute",
                "user": "200/minute",
                "login_burst": "3/minute",
                "password_reset": "2/minute",
                "register": "2/minute",
            },
        },
    )

django.setup()

import json
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from source.modules.auth.api.schema import get_apstudio_openapi_spec
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User
from source.modules.auth.services.password_service import PasswordService


class Phase2DocsAndThrottlingTests(TestCase):
    """
    Automated verification of OpenAPI 3.0.3 Schema, Swagger UI, and Throttling.
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
            first_name="Doc",
            last_name="Tester",
            email="doc.tester@apstudio.com",
            password=PasswordService.hash("InitialPassword123!"),
            role=self.role_user,
            is_email_verified=True,
            is_active=True,
        )

    # ----------------------------------------------------------
    # Test 1: OpenAPI 3.0.3 Schema Generation
    # ----------------------------------------------------------
    def test_01_openapi_schema_endpoint(self):
        print("\n[DOCS TEST 1] Testing OpenAPI 3.0.3 Schema Endpoint (GET /api/schema/)...")
        resp = self.client.get("/api/schema/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/json")

        spec = json.loads(resp.content)
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertEqual(spec["info"]["title"], "AP Studio REST API & Enterprise Auth Engine")
        self.assertEqual(spec["info"]["version"], "0.2.0")

        # Verify Security Schemes
        self.assertIn("BearerAuth", spec["components"]["securitySchemes"])
        self.assertEqual(spec["components"]["securitySchemes"]["BearerAuth"]["scheme"], "bearer")

        # Verify key paths exist
        paths = spec["paths"]
        self.assertIn("/register/", paths)
        self.assertIn("/login/", paths)
        self.assertIn("/token/refresh/", paths)
        self.assertIn("/rbac/roles/", paths)
        self.assertIn("/password/forgot/", paths)
        self.assertIn("/password/reset/", paths)

        print(f"  ✓ OpenAPI 3.0.3 Schema generated successfully with {len(paths)} documented endpoints.")

    # ----------------------------------------------------------
    # Test 2: Interactive Swagger UI Endpoint
    # ----------------------------------------------------------
    def test_02_swagger_ui_endpoint(self):
        print("\n[DOCS TEST 2] Testing Interactive Swagger UI Endpoint (GET /api/docs/)...")
        resp = self.client.get("/api/docs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", resp["Content-Type"])

        html = resp.content.decode("utf-8")
        self.assertIn("AP Studio", html)
        self.assertIn("SwaggerUIBundle", html)
        self.assertIn("/api/schema/", html)
        print("  ✓ Interactive Swagger UI HTML rendered successfully.")

    # ----------------------------------------------------------
    # Test 3: ReDoc Documentation Endpoint
    # ----------------------------------------------------------
    def test_03_redoc_ui_endpoint(self):
        print("\n[DOCS TEST 3] Testing ReDoc Reference Endpoint (GET /api/redoc/)...")
        resp = self.client.get("/api/redoc/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", resp["Content-Type"])

        html = resp.content.decode("utf-8")
        self.assertIn("<redoc", html)
        self.assertIn("/api/schema/", html)
        print("  ✓ ReDoc Reference documentation rendered successfully.")

    # ----------------------------------------------------------
    # Test 4: Login Burst Rate Limiting
    # ----------------------------------------------------------
    def test_04_login_burst_throttling(self):
        print("\n[THROTTLE TEST 4] Testing Login Burst Throttling (3 requests/min limit)...")
        # Rate is set to 3/minute in test settings
        client_ip = "192.168.1.50"

        # 3 allowed requests (will return 400 bad request due to dummy credentials, but not throttled)
        for i in range(3):
            resp = self.client.post(
                "/api/login/",
                {"email": "wrong@apstudio.com", "password": "WrongPassword123!"},
                format="json",
                REMOTE_ADDR=client_ip,
            )
            self.assertNotEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # 4th request MUST trigger HTTP 429
        resp_throttled = self.client.post(
            "/api/login/",
            {"email": "wrong@apstudio.com", "password": "WrongPassword123!"},
            format="json",
            REMOTE_ADDR=client_ip,
        )
        self.assertEqual(resp_throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        print("  ✓ Login burst throttle correctly blocked 4th request with HTTP 429.")

    # ----------------------------------------------------------
    # Test 5: Password Reset Throttling
    # ----------------------------------------------------------
    def test_05_password_reset_throttling(self):
        print("\n[THROTTLE TEST 5] Testing Password Reset Throttling (2 requests/min limit)...")
        client_ip = "192.168.1.60"

        # 2 allowed requests
        for _ in range(2):
            resp = self.client.post(
                "/api/password/forgot/",
                {"email": self.user.email},
                format="json",
                REMOTE_ADDR=client_ip,
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 3rd request MUST trigger HTTP 429
        resp_throttled = self.client.post(
            "/api/password/forgot/",
            {"email": self.user.email},
            format="json",
            REMOTE_ADDR=client_ip,
        )
        self.assertEqual(resp_throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        print("  ✓ Password reset throttle correctly blocked 3rd request with HTTP 429.")

    # ----------------------------------------------------------
    # Test 6: Registration Throttling
    # ----------------------------------------------------------
    def test_06_register_throttling(self):
        print("\n[THROTTLE TEST 6] Testing Registration Throttling (2 requests/min limit)...")
        client_ip = "192.168.1.70"

        # 2 allowed requests
        for i in range(2):
            resp = self.client.post(
                "/api/register/",
                {
                    "first_name": "Test",
                    "last_name": "Bot",
                    "email": f"bot_{i}@apstudio.com",
                    "password": "Password123!",
                },
                format="json",
                REMOTE_ADDR=client_ip,
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # 3rd request MUST trigger HTTP 429
        resp_throttled = self.client.post(
            "/api/register/",
            {
                "first_name": "Test",
                "last_name": "Bot",
                "email": "bot_overflow@apstudio.com",
                "password": "Password123!",
            },
            format="json",
            REMOTE_ADDR=client_ip,
        )
        self.assertEqual(resp_throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        print("  ✓ Registration throttle correctly blocked 3rd account creation with HTTP 429.")

    # ----------------------------------------------------------
    # Test 7: Client IP Isolation in Throttling
    # ----------------------------------------------------------
    def test_07_client_ip_isolation(self):
        print("\n[THROTTLE TEST 7] Testing Client IP Isolation in Throttling...")
        abusive_ip = "192.168.1.99"
        innocent_ip = "192.168.1.100"

        # Exhaust abusive IP's password reset limit (2 requests)
        for _ in range(2):
            self.client.post(
                "/api/password/forgot/",
                {"email": self.user.email},
                format="json",
                REMOTE_ADDR=abusive_ip,
            )

        # Abusive IP is now throttled
        blocked = self.client.post(
            "/api/password/forgot/",
            {"email": self.user.email},
            format="json",
            REMOTE_ADDR=abusive_ip,
        )
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Innocent IP from different address is unaffected
        innocent_resp = self.client.post(
            "/api/password/forgot/",
            {"email": self.user.email},
            format="json",
            REMOTE_ADDR=innocent_ip,
        )
        self.assertEqual(innocent_resp.status_code, status.HTTP_200_OK)
        print("  ✓ Innocent IP remains unaffected while abusive IP is throttled.")


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(["tests.test_phase2_docs_throttling"])
    if failures:
        print(f"\n❌ PHASE 2 DOCS & THROTTLING TESTS FAILED: {failures} failures.")
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 2 OPENAPI & THROTTLING TESTS PASSED 100%!")
        sys.exit(0)
