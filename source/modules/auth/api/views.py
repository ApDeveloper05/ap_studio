"""
------------------------------------------------------------
File: views.py

Module: Authentication API

Purpose:
Pure JSON REST API endpoints for AP Studio:
- Register & 48h Signup Block
- Email OTP Verification
- Standard Login (Returns JWT Pair)
- Emergency 8-Digit OTP Login (Returns JWT Pair)
- Token Refresh & Rotation
- Logout (Session Invalidation)
- User Profile API

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from source.modules.auth.api.authentication import APStudioJWTAuthentication
from source.modules.auth.api.permissions import (
    IsAdminRole,
    IsEmailVerified,
    IsManagerRole,
    IsOwnerOrAdmin,
    require_roles,
)
from source.modules.auth.api.serializers import (
    AssignRoleSerializer,
    LoginOTPRequestSerializer,
    LoginOTPVerifySerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from source.modules.auth.models.user import User
from source.modules.auth.services.jwt_service import JWTService
from source.modules.auth.services.login_service import LoginService
from source.modules.auth.services.register_service import RegisterService
from source.modules.auth.services.role_service import RoleService
from source.modules.auth.services.session_service import SessionService


def _get_client_metadata(request) -> tuple[str, str]:
    """Helper to extract IP address and User-Agent."""
    ip = request.META.get("REMOTE_ADDR", "")
    agent = request.META.get("HTTP_USER_AGENT", "")
    return ip, agent


# ==========================================================
# 1. Registration & Email Verification
# ==========================================================

class RegisterAPIView(APIView):
    """
    POST /api/auth/register/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        ip, agent = _get_client_metadata(request)
        result = RegisterService.register(
            first_name=serializer.validated_data["first_name"],
            last_name=serializer.validated_data["last_name"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            ip_address=ip,
            user_agent=agent,
        )

        if not result["success"]:
            # 48h hard block response
            if result.get("code") == "REGISTRATION_BLOCKED_48H":
                return Response(result, status=status.HTTP_423_LOCKED)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        user = result["data"]
        return Response(
            {
                "success": True,
                "message": result["message"],
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    """
    POST /api/auth/verify-email/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        entered_otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        ip, agent = _get_client_metadata(request)
        result = RegisterService.verify_email(
            user=user,
            entered_otp=entered_otp,
            ip_address=ip,
            user_agent=agent,
        )

        if not result["success"]:
            if result.get("code") == "REGISTRATION_BLOCKED_48H":
                return Response(result, status=status.HTTP_423_LOCKED)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "success": True,
                "code": result.get("code"),
                "message": result.get("message"),
                "data": UserSerializer(result["data"]).data if result.get("data") else None,
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# 2. Login & JWT Generation
# ==========================================================

class LoginAPIView(APIView):
    """
    POST /api/auth/login/
    Returns: Access Token (15 min) + Refresh Token (7 days).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        ip, agent = _get_client_metadata(request)
        result = LoginService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            ip_address=ip,
            user_agent=agent,
        )

        if not result["success"]:
            code = result.get("code")
            if code == "ACCOUNT_SEIZED_24H":
                return Response(result, status=status.HTTP_423_LOCKED)
            if code == "DEVICE_LOCKED":
                return Response(result, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response(result, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT Token Pair tied to session
        session = result["data"]
        token_pair = JWTService.generate_token_pair(user=session.user, session=session)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": token_pair,
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# 3. Emergency 8-Digit OTP Login
# ==========================================================

class LoginOTPRequestAPIView(APIView):
    """
    POST /api/auth/login-otp/request/
    Dispatches 8-digit emergency code to user's email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginOTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        ip, agent = _get_client_metadata(request)
        result = LoginService.request_login_otp(
            email=serializer.validated_data["email"],
            ip_address=ip,
            user_agent=agent,
        )

        if not result["success"] and result.get("code") == "ACCOUNT_SEIZED_24H":
            return Response(result, status=status.HTTP_423_LOCKED)

        return Response(result, status=status.HTTP_200_OK)


class LoginOTPVerifyAPIView(APIView):
    """
    POST /api/auth/login-otp/verify/
    Verifies 8-digit emergency code. 3 failures -> 24h freeze.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginOTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        ip, agent = _get_client_metadata(request)
        result = LoginService.verify_login_otp(
            email=serializer.validated_data["email"],
            entered_otp=serializer.validated_data["otp"],
            ip_address=ip,
            user_agent=agent,
        )

        if not result["success"]:
            if result.get("code") == "ACCOUNT_SEIZED_24H":
                return Response(result, status=status.HTTP_423_LOCKED)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT Token Pair
        session = result["data"]
        token_pair = JWTService.generate_token_pair(user=session.user, session=session)

        return Response(
            {
                "success": True,
                "message": "8-Digit OTP verified. Login successful.",
                "data": token_pair,
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# 4. Token Refresh & Logout
# ==========================================================

class RefreshTokenAPIView(APIView):
    """
    POST /api/auth/token/refresh/
    Rotates refresh token and issues fresh access token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data["refresh_token"]
        ok, msg, token_pair = JWTService.refresh_access_token(refresh_token)

        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "success": True,
                "message": msg,
                "data": token_pair,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/
    Destroys active session & terminates tokens.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Invalidate active session
        auth_header = request.headers.get("Authorization", "")
        if "Bearer " in auth_header:
            token = auth_header.split(" ")[1]
            is_valid, _, payload = JWTService.decode(token)
            if is_valid and payload:
                session_token = payload.get("session_token")
                if session_token:
                    SessionService.destroy(session_token)

        return Response(
            {"success": True, "message": "Successfully logged out. Session terminated."},
            status=status.HTTP_200_OK,
        )


# ==========================================================
# 5. Authenticated User Profile API
# ==========================================================

class UserProfileAPIView(APIView):
    """
    GET /api/auth/me/
    Requires: Authorization: Bearer <access_token>
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# 6. Role-Based Access Control (RBAC) APIs
# ==========================================================

class RoleListAPIView(APIView):
    """
    GET /api/rbac/roles/
    List all system roles available in AP Studio.
    Requires: Valid JWT Bearer Token.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = RoleService.list_roles()
        serializer = RoleSerializer(roles, many=True)
        return Response(
            {
                "success": True,
                "count": roles.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AssignRoleAPIView(APIView):
    """
    POST /api/rbac/assign-role/
    Assign a new role to an existing user.
    Requires: Valid JWT Bearer Token with Admin role.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AssignRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = serializer.validated_data.get("user_id")
        email = serializer.validated_data.get("email")
        target_role = serializer.validated_data["role_name"]

        target_user = None
        if user_id:
            target_user = User.objects.filter(id=user_id, is_active=True).first()
        elif email:
            target_user = User.objects.filter(email__iexact=email, is_active=True).first()

        if not target_user:
            return Response(
                {
                    "success": False,
                    "code": "USER_NOT_FOUND",
                    "message": "Target user was not found or is deactivated.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        result = RoleService.assign_role(
            user=target_user,
            role_name=target_role,
            assigned_by=request.user,
        )

        if not result["success"]:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class AdminOnlyDemoAPIView(APIView):
    """
    GET /api/rbac/admin-only/
    Demonstration endpoint strictly restricted to users with Admin role.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": f"Welcome, Admin {request.user.first_name}! You have verified administrator access.",
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class ManagerAccessDemoAPIView(APIView):
    """
    GET /api/rbac/manager-only/
    Demonstration endpoint accessible by both Managers and Admins.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated, IsManagerRole]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": f"Welcome, {request.user.first_name}! Manager/Admin access confirmed.",
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class VerifiedUserOnlyDemoAPIView(APIView):
    """
    GET /api/rbac/verified-only/
    Demonstration endpoint requiring email verification.
    """
    authentication_classes = [APStudioJWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": f"Access granted for verified user: {request.user.email}.",
                "is_email_verified": True,
            },
            status=status.HTTP_200_OK,
        )
