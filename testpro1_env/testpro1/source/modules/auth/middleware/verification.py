"""
------------------------------------------------------------
File: verification.py

Module: Authentication Middleware

Purpose:
Middleware to enforce email verification for specific routes.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages


class VerificationMiddleware(MiddlewareMixin):
    """
    Middleware to ensure authenticated users have verified their emails.
    """

    def process_request(self, request):
        """
        Check if user is verified before accessing protected routes.
        """
        if getattr(request, 'user', None) and not getattr(request.user, 'is_email_verified', False):
            # Define allowed paths for unverified users
            
            allowed_paths = []
            
            if request.user and request.user.id:
                allowed_paths.append(reverse('auth:verify_email', kwargs={'user_id': request.user.id}))
                
            allowed_paths.append(reverse('auth:logout'))
            
            if request.path not in allowed_paths and not request.path.startswith('/admin/'):
                messages.warning(request, "Please verify your email to access this page.")
                if request.user and request.user.id:
                    return redirect("auth:verify_email", user_id=request.user.id)
                return redirect("auth:login")
