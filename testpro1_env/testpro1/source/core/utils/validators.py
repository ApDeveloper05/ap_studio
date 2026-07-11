"""
------------------------------------------------------------
File: validators.py

Module: Core Utilities

Purpose:
Provide reusable validation utilities for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import re


# ==========================================================
# Validation Functions
# ==========================================================

def is_valid_project_name(project_name: str) -> bool:
    """
    Validate project name.
    """

    pattern = r"^[A-Za-z][A-Za-z0-9_]*$"

    return bool(re.fullmatch(pattern, project_name))


def is_valid_email(email: str) -> bool:
    """
    Validate email address.
    """

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return bool(re.fullmatch(pattern, email))


def is_valid_package_name(package_name: str) -> bool:
    """
    Validate Python package name.
    """

    pattern = r"^[a-z][a-z0-9_]*$"

    return bool(re.fullmatch(pattern, package_name))