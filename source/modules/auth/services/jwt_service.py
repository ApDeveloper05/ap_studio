"""
------------------------------------------------------------
File: jwt_service.py

Module: Authentication Services

Purpose:
Cryptographically secure, zero-external-dependency RFC 7519 JSON Web
Token (JWT) engine for AP Studio API & mobile ecosystem.
Supports HS256 Access Tokens & Rotating Refresh Tokens with instant
global revocation via SessionService integration.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone

from source.modules.auth.models.session import Session
from source.modules.auth.models.user import User
from source.modules.auth.services.session_service import SessionService


class JWTService:
    """
    Cryptographic HS256 JSON Web Token Engine.
    """

    ALGORITHM = "HS256"
    ACCESS_TOKEN_LIFETIME_MINUTES = getattr(settings, "JWT_ACCESS_LIFETIME_MINUTES", 15)
    REFRESH_TOKEN_LIFETIME_DAYS = getattr(settings, "JWT_REFRESH_LIFETIME_DAYS", 7)

    @classmethod
    def _get_signing_key(cls) -> bytes:
        """
        Derive HMAC signing key from Django SECRET_KEY.
        """
        secret = getattr(settings, "SECRET_KEY", "ap-studio-default-secret-key-change-in-prod")
        return secret.encode("utf-8")

    @classmethod
    def _base64url_encode(cls, data: bytes) -> str:
        """
        URL-safe Base64 encode without padding.
        """
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @classmethod
    def _base64url_decode(cls, data: str) -> bytes:
        """
        URL-safe Base64 decode with reconstructed padding.
        """
        padding = "=" * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ""
        return base64.urlsafe_b64decode(f"{data}{padding}".encode("utf-8"))

    @classmethod
    def _create_signature(cls, header_b64: str, payload_b64: str) -> str:
        """
        Compute HMAC-SHA256 signature for header and payload.
        """
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(cls._get_signing_key(), signing_input, hashlib.sha256).digest()
        return cls._base64url_encode(signature)

    @classmethod
    def encode(cls, payload: dict[str, Any]) -> str:
        """
        Encode payload dictionary into a standard JWT string.
        """
        header = {"alg": cls.ALGORITHM, "typ": "JWT"}
        header_b64 = cls._base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = cls._base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature_b64 = cls._create_signature(header_b64, payload_b64)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @classmethod
    def decode(cls, token: str) -> tuple[bool, str, dict[str, Any] | None]:
        """
        Validate signature and expiration of a JWT string.
        Returns (is_valid: bool, error_message: str, payload: dict | None).
        """
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return False, "Malformed token structure.", None

            header_b64, payload_b64, signature_b64 = parts

            # 1. Verify signature in constant time
            expected_signature = cls._create_signature(header_b64, payload_b64)
            if not hmac.compare_digest(signature_b64, expected_signature):
                return False, "Invalid cryptographic signature.", None

            # 2. Decode payload
            payload_bytes = cls._base64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))

            # 3. Check expiration
            exp = payload.get("exp")
            if exp is not None and time.time() > exp:
                return False, "Token has expired.", None

            return True, "Valid", payload

        except Exception as e:
            return False, f"Token decode error: {str(e)}", None

    # ==========================================================
    # Token Pair Generation & Lifecycle
    # ==========================================================

    @classmethod
    def generate_token_pair(
        cls,
        *,
        user: User,
        session: Session,
    ) -> dict[str, Any]:
        """
        Generate Access Token (15 min) and Rotating Refresh Token (7 days).
        Tied to active Session for instantaneous multi-device killswitch support.
        """
        now = int(time.time())
        access_exp = now + (cls.ACCESS_TOKEN_LIFETIME_MINUTES * 60)
        refresh_exp = now + (cls.REFRESH_TOKEN_LIFETIME_DAYS * 86400)

        # Access Token Payload
        access_payload = {
            "token_type": "access",
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.role_name if user.role else "user",
            "session_token": session.session_token,
            "iat": now,
            "exp": access_exp,
        }

        # Refresh Token Payload
        refresh_payload = {
            "token_type": "refresh",
            "user_id": str(user.id),
            "session_token": session.session_token,
            "iat": now,
            "exp": refresh_exp,
        }

        return {
            "access_token": cls.encode(access_payload),
            "refresh_token": cls.encode(refresh_payload),
            "token_type": "Bearer",
            "expires_in": cls.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.role_name if user.role else "user",
            },
        }

    @classmethod
    def refresh_access_token(
        cls,
        refresh_token: str,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        """
        Validate refresh token, verify active session in DB, and rotate token pair.
        If session was killed by 24h freeze or logout, refresh is immediately rejected.
        """
        is_valid, err, payload = cls.decode(refresh_token)
        if not is_valid or not payload:
            return False, f"Invalid refresh token: {err}", None

        if payload.get("token_type") != "refresh":
            return False, "Provided token is not a refresh token.", None

        session_token = payload.get("session_token")
        user_id = payload.get("user_id")

        # Verify underlying session is active
        session = SessionService.validate(session_token)
        if not session:
            return False, "Associated session has expired or was terminated.", None

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return False, "User account is inactive or no longer exists.", None

        # Check account seizure
        from source.modules.auth.services.security_service import SecurityService
        is_seized, _ = SecurityService.is_account_seized(user)
        if is_seized:
            return False, "Account is currently frozen under a 24-hour security hold.", None

        # Rotate refresh token / refresh session activity
        SessionService.refresh(session)
        token_pair = cls.generate_token_pair(user=user, session=session)

        return True, "Token refreshed successfully.", token_pair
