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
from source.modules.auth.api.schema import (
    APStudioReDocAPIView,
    APStudioSchemaAPIView,
    APStudioSwaggerUIAPIView,
)
from source.modules.auth.api.throttling import (
    APStudioAnonRateThrottle,
    APStudioUserRateThrottle,
    LoginBurstThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
)

__all__ = [
    "APStudioJWTAuthentication",
    "IsAuthenticatedAPStudio",
    "IsAdminRole",
    "IsManagerRole",
    "IsEmailVerified",
    "IsOwnerOrAdmin",
    "require_roles",
    "APStudioAnonRateThrottle",
    "APStudioUserRateThrottle",
    "LoginBurstThrottle",
    "PasswordResetThrottle",
    "RegisterThrottle",
    "APStudioSchemaAPIView",
    "APStudioSwaggerUIAPIView",
    "APStudioReDocAPIView",
]
