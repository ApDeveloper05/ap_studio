"""
------------------------------------------------------------
File: filesystem.py

Module: Core Utilities

Purpose:
Provide reusable file and directory operations for AP Studio.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from pathlib import Path


# ==========================================================
# Directory Operations
# ==========================================================

def create_directory(directory: Path) -> None:
    """
    Create a directory if it does not already exist.
    """

    directory.mkdir(parents=True, exist_ok=True)


def directory_exists(directory: Path) -> bool:
    """
    Check whether a directory exists.
    """

    return directory.exists() and directory.is_dir()


# ==========================================================
# File Operations
# ==========================================================

def create_file(file_path: Path) -> None:
    """
    Create a file if it does not already exist.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch(exist_ok=True)


def file_exists(file_path: Path) -> bool:
    """
    Check whether a file exists.
    """

    return file_path.exists() and file_path.is_file()


# ==========================================================
# Read & Write Operations
# ==========================================================

def write_file(file_path: Path, content: str) -> None:
    """
    Write content to a file.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def append_file(file_path: Path, content: str) -> None:
    """
    Append content to an existing file.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(content)


def read_file(file_path: Path) -> str:
    """
    Read and return file content.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()