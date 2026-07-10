"""
------------------------------------------------------------
File: profile_service.py

Module: Authentication Services

Purpose:
Handle user profile management.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from source.modules.auth.models.profile import Profile
from source.modules.auth.models.user import User


class ProfileService:
    """
    Handle profile operations.
    """

    @staticmethod
    def create(
        user: User,
        **profile_data,
    ) -> Profile:
        """
        Create a new profile.
        """

        return Profile.objects.create(
            user=user,
            **profile_data,
        )

    @staticmethod
    def get(
        user: User,
    ) -> Profile:
        """
        Return user profile.
        """

        return Profile.objects.get(
            user=user,
        )

    @staticmethod
    def update(
        user: User,
        **profile_data,
    ) -> Profile:
        """
        Update user profile.
        """

        profile = Profile.objects.get(
            user=user,
        )

        for field, value in profile_data.items():

            if hasattr(profile, field):
                setattr(profile, field, value)

        profile.save()

        return profile

    @staticmethod
    def delete(
        user: User,
    ) -> None:
        """
        Soft delete user profile.
        """

        profile = Profile.objects.get(
            user=user,
        )

        profile.soft_delete()