"""
------------------------------------------------------------
File: verified_required.py

Module: Authentication Decorators

Purpose:
Decorator to enforce email verification requirement.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def verified_required(view_func):
    """
    Decorator to ensure the user's email is verified.
    """
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, "user", None)
        
        if not user:
            messages.warning(request, "You must be logged in to access this page.")
            return redirect("auth:login")
            
        if not getattr(user, "is_email_verified", False):
            messages.warning(request, "Please verify your email to access this page.")
            return redirect("auth:verify_email", user_id=user.id)
            
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view
