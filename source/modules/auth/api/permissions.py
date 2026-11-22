"""
------------------------------------------------------------
File: permissions.py

Module: Authentication API

Purpose:
Role-Based Access Control (RBAC) permission classes for Django REST Framework.
Provides declarative permissions for:
- AP Studio JWT Authenticated users
- Admin / Manager role enforcement
- Dynamic multi-role requirements
- Email verification enforcement
- Object-level ownership & admin override

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from typing import Type
from rest_framework.permissions import BasePermission


class IsAuthenticatedAPStudio(BasePermission):
    """
    Ensure the request is authenticated via AP Studio JWT.
    """
    message = "Authentication required. Please provide a valid Bearer token."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "is_active", False))


class IsAdminRole(BasePermission):
    """
    Permission check strictly requiring the 'admin' role.
    """
    message = "Access denied. Administrator privileges required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return getattr(user, "is_admin", False)


class IsManagerRole(BasePermission):
    """
    Permission check requiring 'manager' or 'admin' role.
    """
    message = "Access denied. Manager or Administrator privileges required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return getattr(user, "is_manager", False)


class IsEmailVerified(BasePermission):
    """
    Permission check requiring the user's email to be verified.
    """
    message = "Access denied. Email verification required before performing this action."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(getattr(user, "is_email_verified", False))


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission allowing users to access/edit their own resources,
    or administrators to access any resource.
    """
    message = "Access denied. You can only view or modify your own records."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))

    def has_object_permission(self, request, view, obj) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        # Admin override
        if getattr(user, "is_admin", False):
            return True

        # Direct user object
        if obj == user:
            return True

        # ForeignKey or attribute check: obj.user == user
        if hasattr(obj, "user") and getattr(obj, "user") == user:
            return True

        # ID comparison: obj.user_id == user.id
        if hasattr(obj, "user_id") and str(getattr(obj, "user_id")) == str(user.id):
            return True

        return False


def require_roles(*allowed_roles: str) -> Type[BasePermission]:
    """
    Dynamic RBAC permission factory.
    Creates a DRF BasePermission subclass enforcing membership in `allowed_roles`.

    Usage:
        permission_classes = [IsAuthenticatedAPStudio, require_roles("admin", "manager")]
    """
    roles_list = [r.strip().lower() for r in allowed_roles if r.strip()]
    roles_display = ", ".join(roles_list)

    class DynamicRolePermission(BasePermission):
        message = f"Access denied. Required role: {roles_display}."

        def has_permission(self, request, view) -> bool:
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                return False
            if not hasattr(user, "has_role"):
                return False
            return user.has_role(*roles_list)

    DynamicRolePermission.__name__ = f"RequireRole_{'_'.join(roles_list)}"
    return DynamicRolePermission
