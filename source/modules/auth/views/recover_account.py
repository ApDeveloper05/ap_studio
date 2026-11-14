"""
------------------------------------------------------------
File: recover_account.py

Module: Authentication Views

Purpose:
Handle automated account unfreezing and re-verification after
the 24-hour security seizure period completes.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.models.otp import OTPType
from source.modules.auth.models.security import SeizedAccount
from source.modules.auth.services.email_service import EmailService
from source.modules.auth.services.otp_service import OTPService
from source.modules.auth.services.security_service import SecurityService


def recover_account(request, token: str):
    """
    Handle automated recovery email link clicked by the user.
    Step 1: Validate recovery token & check if 24h freeze period has elapsed.
    Step 2: Dispatch fresh verification OTP to verify ownership.
    Step 3: Unfreeze and restore active account status.
    """
    try:
        seizure = SeizedAccount.objects.get(
            recovery_token=token,
            is_recovered=False,
        )
    except SeizedAccount.DoesNotExist:
        messages.error(request, "Invalid or expired recovery link.")
        return redirect("auth:login")

    # Check if 24 hours have actually elapsed
    if seizure.is_currently_seized:
        return render(
            request,
            "auth/seized_countdown.html",
            {
                "email": seizure.email,
                "remaining_formatted": seizure.remaining_formatted,
                "remaining_seconds": seizure.remaining_seconds,
            },
        )

    user = seizure.user

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        # Fetch latest unlock OTP
        otp_record = user.otps.filter(
            otp_type=OTPType.ACCOUNT_UNLOCK,
            is_verified=False,
        ).order_by("-created_at").first()

        if not otp_record:
            messages.error(request, "No active unlock code found. Please request a new one.")
            return render(request, "auth/recover_account.html", {"user": user, "token": token})

        success, status_code = OTPService.verify(
            otp_object=otp_record,
            entered_otp=entered_otp,
            ip_address=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if not success:
            messages.error(request, "Invalid security code. Please try again.")
            return render(request, "auth/recover_account.html", {"user": user, "token": token})

        # Complete recovery
        ok, msg, _ = SecurityService.complete_account_recovery(recovery_token=token)
        if ok:
            messages.success(request, "Your account has been successfully unlocked and verified! You can now log in.")
            return redirect("auth:login")

        messages.error(request, msg)
        return redirect("auth:login")

    # GET Request: Generate unlock OTP and send
    unlock_otp = OTPService.generate(user=user, otp_type=OTPType.ACCOUNT_UNLOCK)
    EmailService.send_email(
        subject="AP Studio Account Unlock Verification Code",
        message=(
            f"Hi {user.first_name},\n\n"
            f"Your account unlock verification OTP is: {unlock_otp.otp}\n\n"
            "Enter this code on the recovery page to complete unfreezing your account."
        ),
        recipient=user.email,
    )

    return render(
        request,
        "auth/recover_account.html",
        {
            "user": user,
            "token": token,
        },
    )
