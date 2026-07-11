"""
------------------------------------------------------------
File: authentication.py

Module: Authentication Middleware

Purpose:
Middleware to authenticate users via session tokens.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.utils.deprecation import MiddlewareMixin
from source.modules.auth.models.session import Session
from django.utils import timezone


class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to attach user to request based on session token.
    """

    def process_request(self, request):
        """
        Process the incoming request and authenticate user.
        """
        request.user = None
        request.auth_session = None

        session_token = request.session.get("session_token")

        if session_token:
            try:
                session = Session.objects.select_related("user").get(
                    session_token=session_token,
                    is_active=True,
                )
                
                # Check expiration
                if session.expires_at and session.expires_at < timezone.now():
                    session.is_active = False
                    session.save(update_fields=["is_active"])
                    del request.session["session_token"]
                else:
                    request.user = session.user
                    request.auth_session = session
                    
            except Session.DoesNotExist:
                # Invalid session token, clean it up
                del request.session["session_token"]
