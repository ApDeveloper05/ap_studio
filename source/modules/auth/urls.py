"""
------------------------------------------------------------
File: urls.py

Module: Authentication URLs

Purpose:
Map authentication URLs to their respective views.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.urls import include, path

from source.modules.auth.views.register import register
from source.modules.auth.views.login import login
from source.modules.auth.views.logout import logout
from source.modules.auth.views.profile import profile
from source.modules.auth.views.verify_email import verify_email
from source.modules.auth.views.forgot_password import forgot_password
from source.modules.auth.views.reset_password import reset_password
from source.modules.auth.views.login_otp import login_with_otp
from source.modules.auth.views.recover_account import recover_account


app_name = "auth"

urlpatterns = [
    # REST API Endpoints (Mobile / React / Next.js)
    path("api/", include("source.modules.auth.api.urls")),

    # Server-Rendered HTML Views
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("login-otp/", login_with_otp, name="login_otp"),
    path("logout/", logout, name="logout"),
    path("profile/", profile, name="profile"),
    path("verify-email/<uuid:user_id>/", verify_email, name="verify_email"),
    path("forgot-password/", forgot_password, name="forgot_password"),
    path("reset-password/", reset_password, name="reset_password"),
    path("recover-account/<str:token>/", recover_account, name="recover_account"),
]
