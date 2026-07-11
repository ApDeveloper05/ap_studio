"""
------------------------------------------------------------
File: role.py

Module: Authentication Models

Purpose:
Store all user roles used by AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.db import models

from source.modules.auth.models.base import BaseModel


# ==========================================================
# Role Model
# ==========================================================

class Role(BaseModel):
    """
    Store user roles.
    """

    role_name = models.CharField(
        max_length=50,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "aps_roles"

    def __str__(self) -> str:
        return self.role_name