"""
------------------------------------------------------------
File: authentication.py

Module: Authentication API

Purpose:
Django REST Framework authentication class for AP Studio JWT engine.
Validates 'Authorization: Bearer <token>' headers.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from rest_framework import authentication
from rest_framework import exceptions

from source.modules.auth.models.user import User
from source.modules.auth.services.jwt_service import JWTService
from source.modules.auth.services.session_service import SessionService


class APStudioJWTAuthentication(authentication.BaseAuthentication):
    """
    Authenticate requests using AP Studio JWT Access Tokens.
    Header format:
        Authorization: Bearer <access_token>
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed("Authorization header must be formatted as: Bearer <token>")

        token = parts[1]
        is_valid, err_msg, payload = JWTService.decode(token)

        if not is_valid or not payload:
            raise exceptions.AuthenticationFailed(f"Invalid or expired token: {err_msg}")

        if payload.get("token_type") != "access":
            raise exceptions.AuthenticationFailed("Invalid token type. Access token expected.")

        user_id = payload.get("user_id")
        session_token = payload.get("session_token")

        # Verify underlying session is still alive
        if session_token:
            session = SessionService.validate(session_token)
            if not session:
                raise exceptions.AuthenticationFailed("Session has been terminated or expired across devices.")

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found or account is deactivated.")

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
