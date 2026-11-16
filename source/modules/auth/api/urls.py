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
    LoginAPIView,
    LoginOTPRequestAPIView,
    LoginOTPVerifyAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
    UserProfileAPIView,
    VerifyEmailAPIView,
)

app_name = "auth_api"

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="api_verify_email"),
    path("login/", LoginAPIView.as_view(), name="api_login"),
    path("login-otp/request/", LoginOTPRequestAPIView.as_view(), name="api_login_otp_request"),
    path("login-otp/verify/", LoginOTPVerifyAPIView.as_view(), name="api_login_otp_verify"),
    path("token/refresh/", RefreshTokenAPIView.as_view(), name="api_token_refresh"),
    path("logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("me/", UserProfileAPIView.as_view(), name="api_user_profile"),
]
