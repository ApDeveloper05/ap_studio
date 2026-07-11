"""
------------------------------------------------------------
File: admin.py

Module: Authentication Admin

Purpose:
Register authentication models in the Django admin interface.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import admin

from source.modules.auth.models.user import User
from source.modules.auth.models.role import Role
from source.modules.auth.models.profile import Profile
from source.modules.auth.models.session import Session
from source.modules.auth.models.otp import OTP
from source.modules.auth.models.login_attempt import LoginAttempt
from source.modules.auth.models.email_verification import EmailVerification


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_email_verified", "created_at")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_active", "is_email_verified", "role")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "created_at")
    search_fields = ("role_name",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__email",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "created_at", "is_active")
    list_filter = ("is_active",)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp_type", "created_at", "expires_at", "is_used")
    list_filter = ("otp_type", "is_used")


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("email", "ip_address", "is_successful", "created_at")
    list_filter = ("is_successful", "created_at")


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "verified_at", "is_verified")
    list_filter = ("is_verified",)
