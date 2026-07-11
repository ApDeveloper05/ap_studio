"""
------------------------------------------------------------
File: forgot_password.py

Module: Authentication Views

Purpose:
Handle forgot password requests.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.forms.forgot_password import ForgotPasswordForm
from source.modules.auth.models.user import User
from source.modules.auth.models.otp import OTPType
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.email_service import EmailService


def forgot_password(request):
    """
    Handle forgot password request.
    """

    if request.method == "POST":

        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            
            email = form.cleaned_data["email"]

            try:
                user = User.objects.get(email=email)
                
                otp = OTPService.generate(
                    user=user,
                    otp_type=OTPType.PASSWORD_RESET,
                )
                
                email_sent = EmailService.send_password_reset_email(
                    recipient=user.email,
                    otp=otp.otp,
                )
                
                if email_sent:
                    messages.success(
                        request,
                        "Password reset email sent successfully.",
                    )
                    return redirect("auth:reset_password")
                else:
                    messages.error(
                        request,
                        "Failed to send password reset email.",
                    )
            
            except User.DoesNotExist:
                messages.error(
                    request,
                    "User with this email does not exist.",
                )
    else:

        form = ForgotPasswordForm()

    return render(
        request,
        "auth/forgot_password.html",
        {
            "form": form,
        },
    )
