"""
------------------------------------------------------------
File: login_required.py

Module: Authentication Decorators

Purpose:
Decorator to enforce login requirement.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_required(view_func):
    """
    Decorator to ensure the user is logged in.
    """
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, "user", None):
            messages.warning(request, "You must be logged in to access this page.")
            return redirect("auth:login")
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view
