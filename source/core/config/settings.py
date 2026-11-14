"""
------------------------------------------------------------
File: settings.py

Module: Core Configuration

Purpose:
Store all global configuration used by AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from pathlib import Path


# ==========================================================
# Project Information
# ==========================================================

PROJECT_NAME = "AP Studio"

PROJECT_FULL_NAME = "Aryan Parmar Studio"

VERSION = "0.1.0"

AUTHOR = "Aryan Parmar"

STATUS = "Under Development"


# ==========================================================
# Paths
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parents[3]

SOURCE_DIR = ROOT_DIR / "source"

FRAMEWORKS_DIR = SOURCE_DIR / "frameworks"

MODULES_DIR = SOURCE_DIR / "modules"

DOCS_DIR = ROOT_DIR / "docs"

ASSETS_DIR = ROOT_DIR / "assets"

TESTS_DIR = ROOT_DIR / "tests"


# ==========================================================
# Supported Frameworks
# ==========================================================

SUPPORTED_FRAMEWORKS = (
    "django",
)


# ==========================================================
# Supported Databases
# ==========================================================

SUPPORTED_DATABASES = (
    "sqlite",
    "mysql",
    "postgresql",
)


# ==========================================================
# Future Configuration Flags
# ==========================================================

ENABLE_GUI = False

ENABLE_AI = False

ENABLE_PLUGIN_SYSTEM = False


# ==========================================================
# Authentication Settings
# ==========================================================

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"

PASSWORD_HASH_ITERATIONS = 100_000

PASSWORD_SALT_LENGTH = 32

OTP_LENGTH = 6

LOGIN_OTP_LENGTH = 8

OTP_EXPIRY_MINUTES = 15

OTP_MAX_RETRY = 3

SIGNUP_BLOCK_HOURS = 48

ACCOUNT_SEIZE_HOURS = 24

DEVICE_LOCKOUT_INITIAL_MINUTES = 15

DEVICE_LOCKOUT_EXTENDED_HOURS = 3

SESSION_EXPIRY_HOURS = 24

MAX_LOGIN_ATTEMPTS = 3


# ==========================================================
# Email Settings (Testing Mode)
# ==========================================================

# Use console backend to print emails/OTPs to the terminal during testing.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = "testing@apstudio.com"