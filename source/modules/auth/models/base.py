"""
------------------------------------------------------------
File: base.py

Module: Authentication Models

Purpose:
Base model inherited by all AP Studio authentication models.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import uuid

from django.db import models


# ==========================================================
# Base Model
# ==========================================================

class BaseModel(models.Model):
    """
    Common base model for all AP Studio authentication models.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_deleted = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """
        Soft delete the current record.
        """

        self.is_deleted = True
        self.save(update_fields=["is_deleted"])

    def restore(self) -> None:
        """
        Restore a soft deleted record.
        """

        self.is_deleted = False
        self.save(update_fields=["is_deleted"])

    def activate(self) -> None:
        """
        Activate the current record.
        """

        self.is_active = True
        self.save(update_fields=["is_active"])

    def deactivate(self) -> None:
        """
        Deactivate the current record.
        """

        self.is_active = False
        self.save(update_fields=["is_active"])