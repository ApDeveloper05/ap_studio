"""
------------------------------------------------------------
File: login_otp.py

Module: Authentication Views

Purpose:
Handle Emergency Passwordless Login with 8-Digit Cryptographic OTP.
3 failed attempts trigger a 24-hour global account freeze.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from source.modules.auth.services.login_service import LoginService


def login_with_otp(request):
    """
    Two-step 8-digit OTP Login:
    Step 1 (GET / POST with email): Sends 8-digit OTP to user's email.
    Step 2 (POST with email & otp): Verifies 8-digit code and creates session.
    """
    step = request.session.get("login_otp_step", 1)
    target_email = request.session.get("login_otp_email", "")

    if request.method == "POST":
        action = request.POST.get("action", "request_otp")

        ip_address = request.META.get("REMOTE_ADDR", "")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Step 1: Request 8-Digit Code
        if action == "request_otp":
            email = request.POST.get("email", "").strip().lower()
            if not email:
                messages.error(request, "Please enter your registered email address.")
                return render(request, "auth/login_otp.html", {"step": 1})

            response = LoginService.request_login_otp(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if response["success"]:
                request.session["login_otp_step"] = 2
                request.session["login_otp_email"] = email
                messages.success(request, response["message"])
                return render(
                    request,
                    "auth/login_otp.html",
                    {"step": 2, "email": email},
                )

            messages.error(request, response["message"])
            return render(
                request,
                "auth/login_otp.html",
                {"step": 1, "email": email, "error_data": response.get("data")},
            )

        # Step 2: Verify 8-Digit Code
        elif action == "verify_otp":
            entered_otp = request.POST.get("otp", "").strip()
            email = request.POST.get("email", target_email).strip().lower()

            if len(entered_otp) != 8 or not entered_otp.isdigit():
                messages.error(request, "Please enter a valid 8-digit security code.")
                return render(request, "auth/login_otp.html", {"step": 2, "email": email})

            response = LoginService.verify_login_otp(
                email=email,
                entered_otp=entered_otp,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if response["success"]:
                request.session["session_token"] = response["data"].session_token
                # Clear temporary login OTP session state
                request.session.pop("login_otp_step", None)
                request.session.pop("login_otp_email", None)

                messages.success(request, response["message"])
                return redirect("auth:profile")

            # Handle 24h freeze
            if response.get("code") == "ACCOUNT_SEIZED_24H":
                request.session.pop("login_otp_step", None)
                request.session.pop("login_otp_email", None)
                messages.error(request, response["message"])
                return render(
                    request,
                    "auth/login_otp.html",
                    {"step": 1, "is_seized": True, "seizure_data": response.get("data")},
                )

            messages.error(request, response["message"])
            return render(request, "auth/login_otp.html", {"step": 2, "email": email})

    # GET Request
    return render(
        request,
        "auth/login_otp.html",
        {"step": step, "email": target_email},
    )
