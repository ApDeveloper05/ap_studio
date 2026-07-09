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