"""
------------------------------------------------------------
File: session_service.py

Module: Authentication Services

Purpose:
Handle authenticated user sessions.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from datetime import timedelta
import secrets

from django.utils import timezone       

from source.modules.auth.models.session import Session
from source.modules.auth.models.user import User


class SessionService:
    """
    Handle authenticated user sessions.
    """

    SESSION_EXPIRY_HOURS = 24

    @classmethod
    def create(
        cls,
        *,
        user: User,
        ip_address: str,
        user_agent: str,
    ) -> Session:
        """
        Create a new authenticated session.
        """

        session_token = secrets.token_urlsafe(64)

        return Session.objects.create(
            user=user,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=timezone.now()
            + timedelta(hours=cls.SESSION_EXPIRY_HOURS),
            last_activity=timezone.now(),
        )

    @staticmethod
    def validate(
        session_token: str,
    ) -> Session | None:
        """
        Validate session token.
        """

        try:

            session = Session.objects.get(
                session_token=session_token,
                is_expired=False,
            )

        except Session.DoesNotExist:

            return None

        if timezone.now() > session.expires_at:

            session.is_expired = True

            session.save(
                update_fields=[
                    "is_expired",
                ]
            )

            return None

        return session

    @staticmethod
    def refresh(
        session: Session,
    ) -> None:
        """
        Update session activity.
        """

        session.last_activity = timezone.now()

        session.save(
            update_fields=[
                "last_activity",
            ]
        )

    @staticmethod
    def destroy(
        session_token: str,
    ) -> bool:
        """
        Destroy an active session.
        """

        try:

            session = Session.objects.get(
                session_token=session_token,
                is_expired=False,
            )

        except Session.DoesNotExist:

            return False

        session.is_expired = True

        session.save(
            update_fields=[
                "is_expired",
            ]
        )

        return True

    @staticmethod
    def destroy_all_for_user(
        user: User,
    ) -> int:
        """
        Instant Multi-Device Killswitch.
        Destroy all active sessions across all devices for this user.
        """

        return Session.objects.filter(
            user=user,
            is_expired=False,
        ).update(
            is_expired=True,
        )

    @staticmethod
    def destroy_all_for_user(
        user: User,
    ) -> int:
        """
        Instant Multi-Device Killswitch.
        Destroy all active sessions across all devices for this user.
        """

        return Session.objects.filter(
            user=user,
            is_expired=False,
        ).update(
            is_expired=True,
        )

