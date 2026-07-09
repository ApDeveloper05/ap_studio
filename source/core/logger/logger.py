"""
------------------------------------------------------------
File: logger.py

Module: Core Logger

Purpose:
Provide centralized logging for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import logging
from pathlib import Path

from source.core.config.settings import ROOT_DIR


# ==========================================================
# Log Directory
# ==========================================================

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "ap_studio.log"


# ==========================================================
# Logger Configuration
# ==========================================================

LOGGER = logging.getLogger("APStudio")

LOGGER.setLevel(logging.INFO)

if not LOGGER.handlers:

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)


# ==========================================================
# Helper Functions
# ==========================================================

def info(message: str) -> None:
    """
    Log an information message.
    """

    LOGGER.info(message)


def warning(message: str) -> None:
    """
    Log a warning message.
    """

    LOGGER.warning(message)


def error(message: str) -> None:
    """
    Log an error message.
    """

    LOGGER.error(message)


def critical(message: str) -> None:
    """
    Log a critical message.
    """

    LOGGER.critical(message)