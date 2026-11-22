"""
------------------------------------------------------------
File: user.py

Module: Authentication Models

Purpose:
Store user accounts for AP Studio custom authentication.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.db import models

from source.modules.auth.models.base import BaseModel
from source.modules.auth.models.role import Role


# ==========================================================
# User Model
# ==========================================================

class User(BaseModel):
    """
    Custom User Model.
    """

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    email = models.EmailField(
        unique=True,
    )

    password = models.CharField(
        max_length=255,
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    failed_login_attempts = models.PositiveIntegerField(
        default=0,
    )

    is_locked = models.BooleanField(
        default=False,
    )

    lock_until = models.DateTimeField(
        blank=True,
        null=True,
    )

    last_login = models.DateTimeField(
        blank=True,
        null=True,
    )

    password_changed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "aps_users"

    @property
    def is_authenticated(self) -> bool:
        """Always return True for User instances (Django & DRF compatibility)."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Always return False for User instances (Django & DRF compatibility)."""
        return False

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return bool(self.role and self.role.role_name.lower() == "admin")

    @property
    def is_manager(self) -> bool:
        """Check if user has manager or admin role."""
        return bool(self.role and self.role.role_name.lower() in ["admin", "manager"])

    def has_role(self, *role_names: str) -> bool:
        """Check if user possesses any of the provided role names (case-insensitive)."""
        if not self.role:
            return False
        current = self.role.role_name.lower()
        return current in [r.lower() for r in role_names]

    def __str__(self) -> str:
        return self.email