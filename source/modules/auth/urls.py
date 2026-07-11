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

from django.urls import path

from source.modules.auth.views.register import register
from source.modules.auth.views.login import login
from source.modules.auth.views.logout import logout
from source.modules.auth.views.profile import profile
from source.modules.auth.views.verify_email import verify_email
from source.modules.auth.views.forgot_password import forgot_password
from source.modules.auth.views.reset_password import reset_password


app_name = "auth"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("profile/", profile, name="profile"),
    path("verify-email/<uuid:user_id>/", verify_email, name="verify_email"),
    path("forgot-password/", forgot_password, name="forgot_password"),
    path("reset-password/", reset_password, name="reset_password"),
]
