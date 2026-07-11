"""
------------------------------------------------------------
File: profile.py

Module: Authentication Views

Purpose:
Handle user profile view and updates.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist

from source.modules.auth.forms.profile import ProfileForm
from source.modules.auth.services.profile_service import ProfileService
from source.modules.auth.decorators.login_required import login_required


@login_required
def profile(request):
    """
    Handle user profile display and updates.
    """
    
    user = request.user
    
    try:
        profile_obj = user.profile
    except ObjectDoesNotExist:
        profile_obj = ProfileService.create(user=user)

    if request.method == "POST":
        
        form = ProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            
            try:
                # Extract user data
                user.first_name = form.cleaned_data.pop("first_name", user.first_name)
                user.last_name = form.cleaned_data.pop("last_name", user.last_name)
                user.save(update_fields=["first_name", "last_name"])
                
                # Update profile with remaining data
                ProfileService.update(
                    user=user,
                    **form.cleaned_data,
                )
                
                messages.success(request, "Profile updated successfully.")
            except Exception as e:
                messages.error(request, f"Profile update failed: {str(e)}")
                
            return redirect("auth:profile")
    else:
        
        initial_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": profile_obj.phone_number,
            "address": profile_obj.address,
            "city": profile_obj.city,
            "state": profile_obj.state,
            "country": profile_obj.country,
            "postal_code": profile_obj.postal_code,
        }
        form = ProfileForm(initial=initial_data)

    return render(
        request,
        "auth/profile.html",
        {
            "user": user,
            "profile": profile_obj,
            "form": form,
        },
    )
