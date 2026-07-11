"""
------------------------------------------------------------
File: __init__.py

Module: Authentication Views

Purpose:
Export all authentication views.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from source.modules.auth.views.register import register
from source.modules.auth.views.login import login
from source.modules.auth.views.logout import logout
from source.modules.auth.views.verify_email import verify_email
from source.modules.auth.views.forgot_password import forgot_password
from source.modules.auth.views.reset_password import reset_password
from source.modules.auth.views.profile import profile

__all__ = [
    "register",
    "login",
    "logout",
    "verify_email",
    "forgot_password",
    "reset_password",
    "profile",
]
