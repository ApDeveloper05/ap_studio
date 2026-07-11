"""
------------------------------------------------------------
File: strings.py

Module: Core Utilities

Purpose:
Provide reusable string utility functions for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import re


# ==========================================================
# String Formatting
# ==========================================================

def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case.
    """

    text = text.strip().replace("-", "_").replace(" ", "_")
    text = re.sub(r"_+", "_", text)

    return text.lower()


def to_pascal_case(text: str) -> str:
    """
    Convert text to PascalCase.
    """

    words = re.split(r"[\s_-]+", text.strip())

    return "".join(word.capitalize() for word in words if word)


def to_title_case(text: str) -> str:
    """
    Convert text to Title Case.
    """

    return text.replace("_", " ").title()


# ==========================================================
# String Validation Helpers
# ==========================================================

def is_blank(text: str) -> bool:
    """
    Check whether a string is empty or contains only whitespace.
    """

    return not text.strip()


def clean_text(text: str) -> str:
    """
    Remove unnecessary whitespace from a string.
    """

    return " ".join(text.split())