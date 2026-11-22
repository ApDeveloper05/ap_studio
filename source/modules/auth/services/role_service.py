"""
------------------------------------------------------------
File: role_service.py

Module: Authentication Services

Purpose:
Role-Based Access Control (RBAC) service for AP Studio.
Handles role queries, role creation, and secure role assignment.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from typing import Optional
from django.db import transaction

from source.core.logger.logger import info, warning
from source.modules.auth.models.role import Role
from source.modules.auth.models.user import User


class RoleService:
    """
    Service for managing roles and role assignments.
    """

    @classmethod
    def get_role(cls, role_name: str) -> Optional[Role]:
        """Fetch role by name (case-insensitive)."""
        return Role.objects.filter(role_name__iexact=role_name, is_active=True).first()

    @classmethod
    def list_roles(cls):
        """List all active roles."""
        return Role.objects.filter(is_active=True).order_by("role_name")

    @classmethod
    def create_role(cls, role_name: str, description: Optional[str] = None) -> Role:
        """Create a new role if not already existing."""
        role, created = Role.objects.get_or_create(
            role_name=role_name.lower().strip(),
            defaults={"description": description or f"Role for {role_name}"},
        )
        return role

    @classmethod
    def assign_role(
        cls,
        *,
        user: User,
        role_name: str,
        assigned_by: Optional[User] = None,
    ) -> dict:
        """
        Assign a new role to an existing user.
        Validates target role existence and ensures atomic assignment.
        """
        target_role = cls.get_role(role_name)
        if not target_role:
            return {
                "success": False,
                "code": "ROLE_NOT_FOUND",
                "message": f"Role '{role_name}' does not exist in the system.",
                "data": None,
            }

        old_role = user.role.role_name if user.role else "None"

        with transaction.atomic():
            user.role = target_role
            user.save(update_fields=["role", "updated_at"])

        assigner_info = assigned_by.email if assigned_by else "System"
        info(f"[RBAC] Role updated for {user.email}: {old_role} -> {target_role.role_name} by {assigner_info}")

        return {
            "success": True,
            "code": "ROLE_ASSIGNED_SUCCESSFULLY",
            "message": f"User role successfully updated to '{target_role.role_name}'.",
            "data": {
                "user_id": str(user.id),
                "email": user.email,
                "previous_role": old_role,
                "new_role": target_role.role_name,
            },
        }
