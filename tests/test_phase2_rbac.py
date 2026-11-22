"""
------------------------------------------------------------
File: test_phase2_rbac.py

Module: AP Studio Phase 2 RBAC Test Suite

Purpose:
Rigorous automated testing for Phase 2 - Sprint 2.2:
Role-Based Access Control (RBAC) & Permissions Engine:
1. Unauthenticated RBAC access denial (HTTP 401 Unauthorized + WWW-Authenticate)
2. Admin-only permission enforcement (HTTP 403 for user vs HTTP 200 for admin)
3. Manager permission enforcement (HTTP 403 for user vs HTTP 200 for manager & admin)
4. Email verification permission enforcement (HTTP 403 for unverified)
5. System roles discovery API (GET /api/rbac/roles/)
6. Secure role assignment API (POST /api/rbac/assign-role/ by Admin)
7. Non-admin role escalation rejection (HTTP 403 Forbidden)
8. Role assignment validation (Invalid role / user handling)
9. Object-level ownership & admin override permission (IsOwnerOrAdmin)
10. Dynamic role permission factory (require_roles)

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
        SECRET_KEY="test-secret-key-for-ap-studio-rbac-testing",
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
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from source.modules.auth.api.permissions import (
    IsAdminRole,
    IsEmailVerified,
    IsManagerRole,
    IsOwnerOrAdmin,
    require_roles,
)
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User
from source.modules.auth.services.jwt_service import JWTService
from source.modules.auth.services.password_service import PasswordService
from source.modules.auth.services.session_service import SessionService


class Phase2RBACEngineTests(TestCase):
    """
    Automated verification of AP Studio RBAC & Permissions Engine.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("migrate", verbosity=0)

        # Seed standard roles
        cls.role_admin, _ = Role.objects.get_or_create(
            role_name="admin", defaults={"description": "System Administrator"}
        )
        cls.role_manager, _ = Role.objects.get_or_create(
            role_name="manager", defaults={"description": "Team Manager"}
        )
        cls.role_user, _ = Role.objects.get_or_create(
            role_name="user", defaults={"description": "Standard User"}
        )

    def setUp(self):
        self.client = APIClient()

        # Helper to create a user and generate tokens
        self.user_regular = self._create_user(
            email="regular.user@apstudio.com",
            role=self.role_user,
            is_email_verified=True,
        )
        self.tokens_regular = self._get_tokens(self.user_regular)

        self.user_manager = self._create_user(
            email="team.manager@apstudio.com",
            role=self.role_manager,
            is_email_verified=True,
        )
        self.tokens_manager = self._get_tokens(self.user_manager)

        self.user_admin = self._create_user(
            email="system.admin@apstudio.com",
            role=self.role_admin,
            is_email_verified=True,
        )
        self.tokens_admin = self._get_tokens(self.user_admin)

    def _create_user(self, email: str, role: Role, is_email_verified: bool = True) -> User:
        return User.objects.create(
            first_name="Test",
            last_name="User",
            email=email,
            password=PasswordService.hash("Password123!"),
            role=role,
            is_email_verified=is_email_verified,
            is_active=True,
        )

    def _get_tokens(self, user: User) -> dict:
        session = SessionService.create(user=user, ip_address="127.0.0.1", user_agent="RBACTestClient/1.0")
        return JWTService.generate_token_pair(user=user, session=session)

    # ----------------------------------------------------------
    # Test 1: Unauthenticated RBAC Access Denial
    # ----------------------------------------------------------
    def test_01_unauthenticated_rbac_denial(self):
        print("\n[RBAC TEST 1] Testing unauthenticated access denial on RBAC endpoints...")
        endpoints = [
            "/api/rbac/roles/",
            "/api/rbac/admin-only/",
            "/api/rbac/manager-only/",
            "/api/rbac/verified-only/",
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertIn("Bearer", resp.headers.get("WWW-Authenticate", ""))
        print("  ✓ All RBAC endpoints strictly return HTTP 401 Unauthorized without token.")

    # ----------------------------------------------------------
    # Test 2: Admin-Only Permission Enforcement
    # ----------------------------------------------------------
    def test_02_admin_only_permission(self):
        print("\n[RBAC TEST 2] Testing Admin-only permission enforcement (GET /api/rbac/admin-only/)...")
        # Regular user attempt -> 403
        user_resp = self.client.get(
            "/api/rbac/admin-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_regular['access_token']}",
        )
        self.assertEqual(user_resp.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✓ Regular user blocked from admin endpoint (HTTP 403).")

        # Manager user attempt -> 403
        mgr_resp = self.client.get(
            "/api/rbac/admin-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_manager['access_token']}",
        )
        self.assertEqual(mgr_resp.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✓ Manager user blocked from admin endpoint (HTTP 403).")

        # Admin attempt -> 200 OK
        admin_resp = self.client.get(
            "/api/rbac/admin-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_admin['access_token']}",
        )
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(admin_resp.data["success"])
        print("  ✓ Admin granted access successfully (HTTP 200).")

    # ----------------------------------------------------------
    # Test 3: Manager Access Permission Enforcement
    # ----------------------------------------------------------
    def test_03_manager_access_permission(self):
        print("\n[RBAC TEST 3] Testing Manager access permission (GET /api/rbac/manager-only/)...")
        # Regular user -> 403
        user_resp = self.client.get(
            "/api/rbac/manager-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_regular['access_token']}",
        )
        self.assertEqual(user_resp.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✓ Regular user blocked from manager endpoint (HTTP 403).")

        # Manager -> 200 OK
        mgr_resp = self.client.get(
            "/api/rbac/manager-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_manager['access_token']}",
        )
        self.assertEqual(mgr_resp.status_code, status.HTTP_200_OK)
        print("  ✓ Manager granted access (HTTP 200).")

        # Admin -> 200 OK (Hierarchy inheritance)
        admin_resp = self.client.get(
            "/api/rbac/manager-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_admin['access_token']}",
        )
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
        print("  ✓ Admin granted access to manager endpoint via hierarchy (HTTP 200).")

    # ----------------------------------------------------------
    # Test 4: Email Verification Permission Enforcement
    # ----------------------------------------------------------
    def test_04_email_verification_permission(self):
        print("\n[RBAC TEST 4] Testing Email Verification permission (GET /api/rbac/verified-only/)...")
        unverified_user = self._create_user(
            email="unverified@apstudio.com",
            role=self.role_user,
            is_email_verified=False,
        )
        tokens_unverified = self._get_tokens(unverified_user)

        # Unverified user -> 403
        resp = self.client.get(
            "/api/rbac/verified-only/",
            HTTP_AUTHORIZATION=f"Bearer {tokens_unverified['access_token']}",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✓ Unverified user blocked from verified-only endpoint (HTTP 403).")

        # Verified user -> 200 OK
        resp_verified = self.client.get(
            "/api/rbac/verified-only/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_regular['access_token']}",
        )
        self.assertEqual(resp_verified.status_code, status.HTTP_200_OK)
        print("  ✓ Verified user allowed access (HTTP 200).")

    # ----------------------------------------------------------
    # Test 5: Role Discovery API (GET /api/rbac/roles/)
    # ----------------------------------------------------------
    def test_05_role_discovery_api(self):
        print("\n[RBAC TEST 5] Testing Role Discovery API (GET /api/rbac/roles/)...")
        resp = self.client.get(
            "/api/rbac/roles/",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_regular['access_token']}",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        roles = [r["role_name"] for r in resp.data["data"]]
        self.assertIn("admin", roles)
        self.assertIn("manager", roles)
        self.assertIn("user", roles)
        print(f"  ✓ Roles discovered via API: {roles}")

    # ----------------------------------------------------------
    # Test 6: Secure Role Assignment by Admin
    # ----------------------------------------------------------
    def test_06_assign_role_by_admin(self):
        print("\n[RBAC TEST 6] Testing Admin role assignment (POST /api/rbac/assign-role/)...")
        self.assertEqual(self.user_regular.role.role_name, "user")

        resp = self.client.post(
            "/api/rbac/assign-role/",
            {"email": self.user_regular.email, "role_name": "manager"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_admin['access_token']}",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Verify in DB
        self.user_regular.refresh_from_db()
        self.assertEqual(self.user_regular.role.role_name, "manager")
        self.assertTrue(self.user_regular.is_manager)
        print(f"  ✓ User role upgraded: user -> manager in database.")

    # ----------------------------------------------------------
    # Test 7: Non-Admin Role Escalation Blocked
    # ----------------------------------------------------------
    def test_07_non_admin_role_escalation_blocked(self):
        print("\n[RBAC TEST 7] Testing non-admin role escalation rejection...")
        target_user = self._create_user(
            email="victim@apstudio.com",
            role=self.role_user,
            is_email_verified=True,
        )

        resp = self.client.post(
            "/api/rbac/assign-role/",
            {"email": target_user.email, "role_name": "admin"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_regular['access_token']}",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        target_user.refresh_from_db()
        self.assertEqual(target_user.role.role_name, "user")
        print("  ✓ Non-admin privilege escalation safely rejected (HTTP 403).")

    # ----------------------------------------------------------
    # Test 8: Role Assignment Validation (Invalid Role / User)
    # ----------------------------------------------------------
    def test_08_assign_role_validation(self):
        print("\n[RBAC TEST 8] Testing Role Assignment validation errors...")
        # Invalid role
        resp = self.client.post(
            "/api/rbac/assign-role/",
            {"email": self.user_regular.email, "role_name": "superhuman"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_admin['access_token']}",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["code"], "ROLE_NOT_FOUND")
        print("  ✓ Nonexistent role rejected with code ROLE_NOT_FOUND.")

        # Invalid user
        resp2 = self.client.post(
            "/api/rbac/assign-role/",
            {"email": "nonexistent@apstudio.com", "role_name": "admin"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_admin['access_token']}",
        )
        self.assertEqual(resp2.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp2.data["code"], "USER_NOT_FOUND")
        print("  ✓ Nonexistent user rejected with code USER_NOT_FOUND.")

    # ----------------------------------------------------------
    # Test 9: Object-Level Ownership & Admin Override (IsOwnerOrAdmin)
    # ----------------------------------------------------------
    def test_09_object_level_permission(self):
        print("\n[RBAC TEST 9] Testing Object-level ownership & admin override...")
        perm = IsOwnerOrAdmin()

        class MockResource:
            def __init__(self, owner):
                self.user = owner

        resource_user1 = MockResource(self.user_regular)

        class MockRequest:
            def __init__(self, user):
                self.user = user

        # User 1 accessing own resource -> Allowed
        self.assertTrue(perm.has_object_permission(MockRequest(self.user_regular), None, resource_user1))
        print("  ✓ Resource owner granted access.")

        # User 2 accessing User 1's resource -> Denied
        other_user = self._create_user(email="other@apstudio.com", role=self.role_user)
        self.assertFalse(perm.has_object_permission(MockRequest(other_user), None, resource_user1))
        print("  ✓ Third-party user denied access.")

        # Admin accessing User 1's resource -> Allowed
        self.assertTrue(perm.has_object_permission(MockRequest(self.user_admin), None, resource_user1))
        print("  ✓ Admin granted access via admin override.")

    # ----------------------------------------------------------
    # Test 10: Dynamic Role Permission Factory (require_roles)
    # ----------------------------------------------------------
    def test_10_dynamic_role_permission_factory(self):
        print("\n[RBAC TEST 10] Testing dynamic require_roles factory...")
        custom_perm_class = require_roles("lead_developer", "manager")
        perm = custom_perm_class()

        class MockReq:
            def __init__(self, user):
                self.user = user

        # Manager has access
        self.assertTrue(perm.has_permission(MockReq(self.user_manager), None))
        # Regular user does not
        self.assertFalse(perm.has_permission(MockReq(self.user_regular), None))
        print("  ✓ Dynamic require_roles('lead_developer', 'manager') verified.")


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(["tests.test_phase2_rbac"])
    if failures:
        print(f"\n❌ PHASE 2 RBAC TESTS FAILED: {failures} failures.")
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 2 RBAC & PERMISSIONS TESTS PASSED 100%!")
        sys.exit(0)
