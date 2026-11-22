"""
------------------------------------------------------------
File: throttling.py

Module: Authentication API

Purpose:
Rate limiting and throttling classes for AP Studio REST API.
Protects endpoints against brute-force attacks, DDoS, and credential stuffing:
- Global Anonymous & Authenticated Rate Throttles
- Login Burst Rate Throttle (5/minute per IP)
- Password Reset Throttle (3/minute per IP)
- Registration Abuse Throttle (10/hour per IP)

Features safe fallback default rates to prevent configuration crashes.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class APStudioAnonRateThrottle(AnonRateThrottle):
    """
    Throttle for unauthenticated client requests across public API endpoints.
    """
    scope = "anon"
    default_rate = "30/minute"

    def get_rate(self):
        try:
            return super().get_rate()
        except Exception:
            return self.default_rate


class APStudioUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated client requests across protected API endpoints.
    """
    scope = "user"
    default_rate = "120/minute"

    def get_rate(self):
        try:
            return super().get_rate()
        except Exception:
            return self.default_rate


class LoginBurstThrottle(SimpleRateThrottle):
    """
    Strict burst rate limit on login attempts to thwart automated credential stuffing.
    Default: 5 requests per minute per IP address.
    """
    scope = "login_burst"
    default_rate = "5/minute"

    def get_rate(self):
        try:
            return super().get_rate()
        except Exception:
            return self.default_rate

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"aps_throttle_login_{ident}"


class PasswordResetThrottle(SimpleRateThrottle):
    """
    Throttle on password reset requests to protect against email flooding and enumeration.
    Default: 3 requests per minute per IP address.
    """
    scope = "password_reset"
    default_rate = "3/minute"

    def get_rate(self):
        try:
            return super().get_rate()
        except Exception:
            return self.default_rate

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"aps_throttle_pwd_reset_{ident}"


class RegisterThrottle(SimpleRateThrottle):
    """
    Throttle on account registration to prevent mass fake account creation.
    Default: 10 requests per hour per IP address.
    """
    scope = "register"
    default_rate = "10/hour"

    def get_rate(self):
        try:
            return super().get_rate()
        except Exception:
            return self.default_rate

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"aps_throttle_reg_{ident}"
