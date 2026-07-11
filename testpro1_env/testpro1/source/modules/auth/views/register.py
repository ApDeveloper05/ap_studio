"""
------------------------------------------------------------
File: register.py

Module: Authentication Views

Purpose:
Handle user registration requests.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.forms.register import RegisterForm
from source.modules.auth.services.register_service import RegisterService


def register(request):
    """
    Handle user registration.
    """

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            response = RegisterService.register(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                role_name=form.cleaned_data["role_name"],
            )

            if response["success"]:

                messages.success(
                    request,
                    response["message"],
                )

                return redirect(
                    "auth:verify_email",
                    user_id=response["data"].id,
                )

            messages.error(
                request,
                response["message"],
            )

    else:

        form = RegisterForm()

    return render(
        request,
        "auth/register.html",
        {
            "form": form,
        },
    )