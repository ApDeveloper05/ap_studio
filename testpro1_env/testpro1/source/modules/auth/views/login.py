"""
------------------------------------------------------------
File: login.py

Module: Authentication Views

Purpose:
Handle user login.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.forms.login import LoginForm
from source.modules.auth.services.login_service import LoginService


def login(request):
    """
    Handle user login.
    """

    if request.method == "POST":

        form = LoginForm(request.POST)

        if form.is_valid():

            response = LoginService.login(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                ip_address=request.META.get(
                    "REMOTE_ADDR",
                    "",
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )

            if response["success"]:

                request.session[
                    "session_token"
                ] = response["data"].session_token

                messages.success(
                    request,
                    response["message"],
                )

                return redirect(
                    "auth:profile",
                )

            messages.error(
                request,
                response["message"],
            )

    else:

        form = LoginForm()

    return render(
        request,
        "auth/login.html",
        {
            "form": form,
        },
    )