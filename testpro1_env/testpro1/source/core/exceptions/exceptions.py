"""
------------------------------------------------------------
File: exceptions.py

Module: Core Exceptions

Purpose:
Define all custom exceptions used across AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""


# ==========================================================
# Base Exception
# ==========================================================

class APStudioError(Exception):
    """
    Base exception for all AP Studio errors.
    """

    def __init__(self, message: str = "An unknown AP Studio error occurred.") -> None:
        super().__init__(message)


# ==========================================================
# Framework Exceptions
# ==========================================================

class FrameworkNotSupportedError(APStudioError):
    """
    Raised when a requested framework is not supported.
    """


class FrameworkNotInstalledError(APStudioError):
    """
    Raised when the required framework is not installed.
    """


# ==========================================================
# Project Exceptions
# ==========================================================

class ProjectAlreadyExistsError(APStudioError):
    """
    Raised when the target project already exists.
    """


class ProjectNotFoundError(APStudioError):
    """
    Raised when a project cannot be found.
    """


# ==========================================================
# Configuration Exceptions
# ==========================================================

class ConfigurationError(APStudioError):
    """
    Raised when configuration is invalid.
    """


# ==========================================================
# Authentication Exceptions
# ==========================================================

class AuthenticationError(APStudioError):
    """
    Raised for authentication related errors.
    """


class OTPVerificationError(AuthenticationError):
    """
    Raised when OTP verification fails.
    """


class EmailVerificationError(AuthenticationError):
    """
    Raised when email verification fails.
    """


# ==========================================================
# CLI Exceptions
# ==========================================================

class CommandNotFoundError(APStudioError):
    """
    Raised when an unknown CLI command is executed.
    """


class InvalidArgumentError(APStudioError):
    """
    Raised when invalid CLI arguments are supplied.
    """