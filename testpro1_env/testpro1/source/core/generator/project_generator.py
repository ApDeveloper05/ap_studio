"""
------------------------------------------------------------
File: project_generator.py

Module: Core Generator

Purpose:
Generate and initialize new AP Studio projects.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from pathlib import Path

from source.core.logger.logger import info
from source.core.utils.filesystem import create_directory


class ProjectGenerator:
    """
    Handles project creation.
    """

    def __init__(self, project_name: str):

        self.project_name = project_name
        self.project_directory = Path(project_name)

    def create(self) -> None:
        """
        Create a new project directory.
        """

        info(f"Creating project : {self.project_name}")

        create_directory(self.project_directory)

        info("Project created successfully.")