"""
AP Studio Authentication REST API Package
"""

from source.modules.auth.api.authentication import APStudioJWTAuthentication
from source.modules.auth.api.permissions import (
    IsAdminRole,
    IsAuthenticatedAPStudio,
    IsEmailVerified,
    IsManagerRole,
    IsOwnerOrAdmin,
    require_roles,
)

__all__ = [
    "APStudioJWTAuthentication",
    "IsAuthenticatedAPStudio",
    "IsAdminRole",
    "IsManagerRole",
    "IsEmailVerified",
    "IsOwnerOrAdmin",
    "require_roles",
]
