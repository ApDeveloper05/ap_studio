"""
------------------------------------------------------------
File: template_generator.py

Module: Core Generator

Purpose:
Generate project files from templates.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from pathlib import Path

from source.core.logger.logger import info
from source.core.utils.filesystem import create_file, write_file


class TemplateGenerator:
    """
    Generate files using predefined templates.
    """

    def __init__(self, project_directory: Path) -> None:
        """
        Initialize template generator.
        """

        self.project_directory = Path(project_directory)

    def create_file(
        self,
        relative_path: str,
        content: str = "",
    ) -> None:
        """
        Create a project file with optional content.
        """

        file_path = self.project_directory / relative_path

        info(f"Creating file : {relative_path}")

        create_file(file_path)

        if content:
            write_file(file_path, content)

        info(f"File '{relative_path}' created successfully.")