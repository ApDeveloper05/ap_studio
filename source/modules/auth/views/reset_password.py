"""
------------------------------------------------------------
File: reset_password.py

Module: Authentication Views

Purpose:
Handle password reset requests.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.forms.reset_password import ResetPasswordForm
from source.modules.auth.models.otp import OTP, OTPType
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.password_service import PasswordService


def reset_password(request):
    """
    Handle password reset.
    """

    if request.method == "POST":

        form = ResetPasswordForm(request.POST)

        if form.is_valid():
            
            otp_code = form.cleaned_data["otp"]
            new_password = form.cleaned_data["password"]
            
            otp_obj = OTP.objects.filter(
                otp=otp_code,
                otp_type=OTPType.PASSWORD_RESET,
                is_verified=False
            ).first()

            if not otp_obj:
                messages.error(request, "Invalid or expired OTP.")
                return render(request, "auth/reset_password.html", {"form": form})

            if OTPService.verify(otp_object=otp_obj, entered_otp=otp_code):
                
                response = PasswordService.reset_password(
                    user=otp_obj.user,
                    new_password=new_password,
                )
                
                if response["success"]:
                    messages.success(
                        request,
                        response["message"],
                    )
                    return redirect("auth:login")
                
                messages.error(
                    request,
                    response["message"],
                )
            else:
                messages.error(
                    request,
                    "Invalid or expired OTP.",
                )
    else:

        form = ResetPasswordForm()

    return render(
        request,
        "auth/reset_password.html",
        {
            "form": form,
        },
    )
