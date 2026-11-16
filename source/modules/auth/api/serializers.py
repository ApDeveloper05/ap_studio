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
