"""
------------------------------------------------------------
File: verify_email.py

Module: Authentication Views

Purpose:
Handle email verification.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.models.user import User
from source.modules.auth.services.register_service import RegisterService


def verify_email(
    request,
    user_id,
):
    """
    Verify user email.
    """

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    if request.method == "POST":

        response = RegisterService.verify_email(
            user,
        )

        if response["success"]:

            messages.success(
                request,
                response["message"],
            )

            return redirect(
                "auth:login",
            )

        messages.error(
            request,
            response["message"],
        )

    return render(
        request,
        "auth/verify_email.html",
        {
            "user": user,
        },
    )