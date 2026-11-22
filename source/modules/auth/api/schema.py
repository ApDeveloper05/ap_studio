"""
------------------------------------------------------------
File: schema.py

Module: Authentication API

Purpose:
Zero-dependency OpenAPI 3.0.3 Schema Generator and Interactive
API Documentation (Swagger UI & ReDoc) for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.http import HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


def get_apstudio_openapi_spec() -> dict:
    """
    Construct complete, standards-compliant OpenAPI 3.0.3 specification
    for all AP Studio REST endpoints without requiring third-party pip dependencies.
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AP Studio REST API & Enterprise Auth Engine",
            "version": "0.2.0",
            "description": (
                "Official REST API documentation for AP Studio by Aryan Parmar.\n\n"
                "Features enterprise security architecture:\n"
                "- RFC 7519 HS256 JWT Access & Rotating Refresh Tokens\n"
                "- 48-Hour Registration Lockout Engine\n"
                "- 24-Hour Account Seizure with Multi-Device Session Killswitch\n"
                "- 8-Digit Emergency Login OTP\n"
                "- Role-Based Access Control (Admin, Manager, User)\n"
                "- Anti-Replay Single-Use Password Reset Engine\n"
                "- Multi-Tier Rate Limiting & Throttling"
            ),
            "contact": {
                "name": "Aryan Parmar (AP Studio)",
                "email": "apdeveloper051106@gmail.com",
            },
            "license": {
                "name": "Proprietary / AP Studio License",
            },
        },
        "servers": [
            {"url": "/api", "description": "Current Environment API Base URL"},
        ],
        "tags": [
            {"name": "Authentication", "description": "User registration, email verification, login & token lifecycle"},
            {"name": "RBAC & Permissions", "description": "Role-Based Access Control, role discovery & assignment"},
            {"name": "Password Management", "description": "Forgot password, secure OTP verification & password reset"},
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Provide AP Studio JWT Access Token as: `Bearer <token>`",
                }
            },
            "schemas": {
                "StandardResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "data": {"type": "object", "nullable": True},
                    },
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "email": {"type": "string", "format": "email"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "role": {"type": "string"},
                        "is_email_verified": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                    },
                },
                "TokenPair": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "token_type": {"type": "string", "example": "Bearer"},
                        "expires_in_minutes": {"type": "integer", "example": 15},
                    },
                },
            },
        },
        "paths": {
            "/register/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register a new user account",
                    "description": "Registers a new user and dispatches a 6-digit email verification OTP. Checks 48h lockout.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["first_name", "last_name", "email", "password"],
                                    "properties": {
                                        "first_name": {"type": "string", "example": "Aryan"},
                                        "last_name": {"type": "string", "example": "Parmar"},
                                        "email": {"type": "string", "format": "email", "example": "developer@apstudio.com"},
                                        "password": {"type": "string", "format": "password", "minLength": 8, "example": "SecurePass123!"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "User created successfully. OTP sent."},
                        "400": {"description": "Validation error or existing email."},
                        "423": {"description": "Registration locked for 48 hours due to prior abuse."},
                    },
                }
            },
            "/verify-email/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Verify email via OTP",
                    "description": "Validates the 6-digit OTP sent to user's email. 3 failed attempts trigger a 48h hard block.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "otp"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "otp": {"type": "string", "example": "123456"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Email verified successfully."},
                        "400": {"description": "Invalid or expired OTP."},
                        "423": {"description": "3 strikes reached. Registration blocked for 48 hours."},
                    },
                }
            },
            "/login/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Standard password login",
                    "description": "Authenticates user with email & password. Returns RFC 7519 JWT access + rotating refresh token pair.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "password"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "password": {"type": "string", "format": "password"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Authenticated successfully. JWT tokens issued."},
                        "400": {"description": "Invalid credentials or unverified email."},
                        "423": {"description": "Account seized or locked."},
                    },
                }
            },
            "/login-otp/request/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Request emergency 8-digit login OTP",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email"],
                                    "properties": {"email": {"type": "string", "format": "email"}},
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "8-Digit Emergency OTP sent."}},
                }
            },
            "/login-otp/verify/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Verify 8-digit emergency login OTP",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "otp"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "otp": {"type": "string", "minLength": 8, "maxLength": 8},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "Verified. JWT tokens issued."}},
                }
            },
            "/token/refresh/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Rotate refresh token & obtain fresh access token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["refresh_token"],
                                    "properties": {"refresh_token": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "New access + refresh token pair issued."},
                        "401": {"description": "Expired or invalidated session."},
                    },
                }
            },
            "/logout/": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Logout & invalidate active session",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": {"description": "Session destroyed. Tokens revoked."}},
                }
            },
            "/me/": {
                "get": {
                    "tags": ["Authentication"],
                    "summary": "Retrieve authenticated user profile",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {"description": "User profile returned."},
                        "401": {"description": "Unauthenticated or invalid Bearer token."},
                    },
                }
            },
            "/rbac/roles/": {
                "get": {
                    "tags": ["RBAC & Permissions"],
                    "summary": "List all active system roles",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": {"description": "List of system roles."}},
                }
            },
            "/rbac/assign-role/": {
                "post": {
                    "tags": ["RBAC & Permissions"],
                    "summary": "Assign role to user (Admin Only)",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["role_name"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "user_id": {"type": "string", "format": "uuid"},
                                        "role_name": {"type": "string", "example": "manager"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Role successfully assigned."},
                        "403": {"description": "Permission denied. Admin privileges required."},
                    },
                }
            },
            "/password/forgot/": {
                "post": {
                    "tags": ["Password Management"],
                    "summary": "Request password reset OTP",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email"],
                                    "properties": {"email": {"type": "string", "format": "email"}},
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "Password reset OTP dispatched."}},
                }
            },
            "/password/verify-otp/": {
                "post": {
                    "tags": ["Password Management"],
                    "summary": "Verify reset OTP and obtain single-use reset token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "otp"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "otp": {"type": "string"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "OTP verified. Single-use reset_token issued."},
                        "423": {"description": "3 strikes reached. Account seized for 24 hours."},
                    },
                }
            },
            "/password/reset/": {
                "post": {
                    "tags": ["Password Management"],
                    "summary": "Reset password with single-use reset token",
                    "description": "Applies anti-replay check and triggers multi-device session killswitch.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["reset_token", "new_password", "confirm_password"],
                                    "properties": {
                                        "reset_token": {"type": "string"},
                                        "new_password": {"type": "string", "format": "password", "minLength": 8},
                                        "confirm_password": {"type": "string", "format": "password", "minLength": 8},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Password reset successful. All active sessions terminated."},
                        "400": {"description": "Invalid token or password mismatch."},
                    },
                }
            },
            "/password/change/": {
                "post": {
                    "tags": ["Password Management"],
                    "summary": "In-session password change for authenticated users",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["current_password", "new_password", "confirm_password"],
                                    "properties": {
                                        "current_password": {"type": "string", "format": "password"},
                                        "new_password": {"type": "string", "format": "password", "minLength": 8},
                                        "confirm_password": {"type": "string", "format": "password", "minLength": 8},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Password changed successfully."},
                        "400": {"description": "Invalid current password or complexity failure."},
                    },
                }
            },
        },
    }


class APStudioSchemaAPIView(APIView):
    """
    GET /api/schema/
    Returns pure OpenAPI 3.0.3 JSON specification for all AP Studio endpoints.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse(get_apstudio_openapi_spec(), json_dumps_params={"indent": 2})


class APStudioSwaggerUIAPIView(APIView):
    """
    GET /api/docs/
    Renders interactive Swagger UI with Authorize Bearer JWT button and Try It Out capability.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AP Studio — REST API Documentation (v0.2.0)</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@5.11.0/favicon-32x32.png" />
  <style>
    body { margin: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .topbar { background-color: #1e293b; padding: 14px 30px; display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #3b82f6; }
    .topbar-brand { color: #ffffff; font-weight: 700; font-size: 20px; display: flex; align-items: center; gap: 10px; }
    .topbar-badge { background-color: #3b82f6; color: white; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
    .swagger-ui .info .title { color: #0ea5e9; }
    .swagger-ui { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .swagger-ui .scheme-container { background: #ffffff; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border-radius: 8px; }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-brand">
      <span>🚀 AP Studio REST API Engine</span>
      <span class="topbar-badge">v0.2.0</span>
    </div>
    <div style="color: #94a3b8; font-size: 14px;">Author: Aryan Parmar</div>
  </div>

  <div id="swagger-ui"></div>

  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      window.ui = SwaggerUIBundle({
        url: "/api/schema/",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout",
        persistAuthorization: true
      });
    };
  </script>
</body>
</html>
"""
        return HttpResponse(html_content, content_type="text/html")


class APStudioReDocAPIView(APIView):
    """
    GET /api/redoc/
    Renders ReDoc three-column technical reference documentation.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        html_content = """<!DOCTYPE html>
<html>
  <head>
    <title>AP Studio API Reference — ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>body { margin: 0; padding: 0; }</style>
  </head>
  <body>
    <redoc spec-url='/api/schema/'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"> </script>
  </body>
</html>
"""
        return HttpResponse(html_content, content_type="text/html")
