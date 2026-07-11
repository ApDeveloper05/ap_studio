"""
------------------------------------------------------------
File: role_required.py

Module: Authentication Decorators

Purpose:
Decorator to enforce role requirements.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    """
    Decorator to ensure the user has a specific role.
    """
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, "user", None)
            
            if not user:
                messages.warning(request, "You must be logged in to access this page.")
                return redirect("auth:login")
                
            if not getattr(user, "role", None) or user.role.role_name not in allowed_roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("auth:profile")
                
            return view_func(request, *args, **kwargs)
            
        return _wrapped_view
    return decorator
