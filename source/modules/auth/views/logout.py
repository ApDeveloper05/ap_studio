"""
------------------------------------------------------------
File: logout.py

Module: Authentication Views

Purpose:
Handle logout.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect

from source.modules.auth.services.login_service import LoginService


def logout(request):
    """
    Logout current user.
    """

    session_token = request.session.get(
        "session_token",
    )

    if session_token:

        LoginService.logout(
            session_token,
        )

        request.session.flush()

    messages.success(
        request,
        "Logout successful.",
    )

    return redirect(
        "auth:login",
    )