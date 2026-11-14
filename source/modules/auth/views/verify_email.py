"""
------------------------------------------------------------
File: verify_email.py

Module: Authentication Views

Purpose:
Handle user email OTP verification with automated 48-hour
registration block protection on 3 failed attempts.

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
from source.modules.auth.services.security_service import SecurityService


def verify_email(
    request,
    user_id,
):
    """
    Verify user email with OTP code.
    """
    user = get_object_or_404(
        User,
        pk=user_id,
    )

    # Check if this email is under active 48h block
    is_blocked, block_record = SecurityService.is_registration_blocked(user.email)
    if is_blocked and block_record:
        return render(
            request,
            "auth/blocked_countdown.html",
            {
                "email": user.email,
                "remaining_formatted": block_record.remaining_formatted,
                "remaining_seconds": block_record.remaining_seconds,
            },
        )

    if request.method == "POST":
        action = request.POST.get("action", "verify")

        # Handle Resend OTP
        if action == "resend":
            resend_resp = RegisterService.resend_verification(user)
            if resend_resp["success"]:
                messages.success(request, resend_resp["message"])
            else:
                messages.error(request, resend_resp["message"])
            return render(request, "auth/verify_email.html", {"user": user})

        # Handle Verify OTP
        entered_otp = request.POST.get("otp", "").strip()
        if not entered_otp:
            messages.error(request, "Please enter the verification OTP code.")
            return render(request, "auth/verify_email.html", {"user": user})

        ip_address = request.META.get("REMOTE_ADDR", "")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        response = RegisterService.verify_email(
            user=user,
            entered_otp=entered_otp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if response["success"]:
            messages.success(
                request,
                response["message"],
            )
            return redirect("auth:login")

        # 48-Hour Hard Block Triggered
        if response.get("code") == "REGISTRATION_BLOCKED_48H":
            messages.error(request, response["message"])
            return render(
                request,
                "auth/blocked_countdown.html",
                {
                    "email": user.email,
                    "remaining_formatted": "48h 00m 00s",
                    "remaining_seconds": 48 * 3600,
                },
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
