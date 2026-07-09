"""
------------------------------------------------------------
File: app_generator.py

Module: Core Generator

Purpose:
Generate application modules inside an AP Studio project.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from pathlib import Path

from source.core.logger.logger import info
from source.core.utils.filesystem import create_directory


class AppGenerator:
    """
    Generate application directories.
    """

    def __init__(self, project_directory: Path) -> None:

        self.project_directory = Path(project_directory)

    def create(self, app_name: str) -> None:
        """
        Create a new application directory.
        """

        application_directory = self.project_directory / app_name

        info(f"Creating application : {app_name}")

        create_directory(application_directory)

        info(f"Application '{app_name}' created successfully.")