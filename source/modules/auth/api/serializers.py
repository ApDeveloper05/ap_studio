"""
------------------------------------------------------------
File: serializers.py

Module: Authentication API

Purpose:
Django REST Framework serializers for AP Studio Auth API.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from rest_framework import serializers

from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for authenticated user profile responses.
    """
    role = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_email_verified",
            "created_at",
        ]


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=10)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=8, min_length=8)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for listing system roles.
    """
    class Meta:
        model = Role
        fields = [
            "id",
            "role_name",
            "description",
            "created_at",
        ]


class AssignRoleSerializer(serializers.Serializer):
    """
    Serializer for admin role assignment endpoint.
    Accepts either user_id or email, plus the desired target role_name.
    """
    user_id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)
    role_name = serializers.CharField(max_length=50)

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("email"):
            raise serializers.ValidationError("Either 'user_id' or 'email' must be provided.")
        return attrs


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset OTP."""
    email = serializers.EmailField()


class VerifyPasswordResetOTPSerializer(serializers.Serializer):
    """Serializer for verifying password reset OTP and obtaining a reset token."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=10)


class ResetPasswordWithTokenSerializer(serializers.Serializer):
    """Serializer for resetting password with single-use reset token."""
    reset_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for authenticated in-session password change."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
