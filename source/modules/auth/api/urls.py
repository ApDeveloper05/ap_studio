"""
------------------------------------------------------------
File: urls.py

Module: Authentication API

Purpose:
Map REST API endpoints for AP Studio authentication engine.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.urls import path

from source.modules.auth.api.views import (
    AdminOnlyDemoAPIView,
    AssignRoleAPIView,
    LoginAPIView,
    LoginOTPRequestAPIView,
    LoginOTPVerifyAPIView,
    LogoutAPIView,
    ManagerAccessDemoAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
    RoleListAPIView,
    UserProfileAPIView,
    VerifiedUserOnlyDemoAPIView,
    VerifyEmailAPIView,
)

app_name = "auth_api"

urlpatterns = [
    # Core Auth Endpoints
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="api_verify_email"),
    path("login/", LoginAPIView.as_view(), name="api_login"),
    path("login-otp/request/", LoginOTPRequestAPIView.as_view(), name="api_login_otp_request"),
    path("login-otp/verify/", LoginOTPVerifyAPIView.as_view(), name="api_login_otp_verify"),
    path("token/refresh/", RefreshTokenAPIView.as_view(), name="api_token_refresh"),
    path("logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("me/", UserProfileAPIView.as_view(), name="api_user_profile"),

    # Role-Based Access Control (RBAC) Endpoints
    path("rbac/roles/", RoleListAPIView.as_view(), name="api_rbac_roles"),
    path("rbac/assign-role/", AssignRoleAPIView.as_view(), name="api_rbac_assign_role"),
    path("rbac/admin-only/", AdminOnlyDemoAPIView.as_view(), name="api_rbac_admin_only"),
    path("rbac/manager-only/", ManagerAccessDemoAPIView.as_view(), name="api_rbac_manager_only"),
    path("rbac/verified-only/", VerifiedUserOnlyDemoAPIView.as_view(), name="api_rbac_verified_only"),
]
