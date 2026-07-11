"""
------------------------------------------------------------
File: apps.py

Module: Authentication App Configuration

Purpose:
Configure the Authentication Django application.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.apps import AppConfig


class AuthConfig(AppConfig):
    """
    Configuration for the auth application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "source.modules.auth"
    verbose_name = "Authentication"

    def ready(self) -> None:
        """
        Execute code when the app is ready.
        Registers signals if available.
        """
        
        try:
            import source.modules.auth.signals
        except ImportError:
            pass
