"""
------------------------------------------------------------
File: configurator.py

Module: Django Framework

Purpose:
Configure Django project settings before project generation.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from dataclasses import dataclass

from source.core.logger.logger import info
from source.core.utils.validators import is_valid_project_name


# ==========================================================
# Django Configuration Model
# ==========================================================

@dataclass(slots=True)
class DjangoConfiguration:
    """
    Stores Django project configuration.
    """

    project_name: str
    app_name: str
    database: str = "sqlite"
    create_virtual_environment: bool = True


# ==========================================================
# Django Configurator
# ==========================================================

class DjangoConfigurator:
    """
    Validate and prepare Django configuration.
    """

    def __init__(self, configuration: DjangoConfiguration) -> None:

        self.configuration = configuration

    def validate(self) -> bool:
        """
        Validate Django configuration.
        """

        info("Validating Django configuration...")

        if not is_valid_project_name(self.configuration.project_name):
            raise ValueError(
                f"Invalid project name: {self.configuration.project_name}"
            )

        if not is_valid_project_name(self.configuration.app_name):
            raise ValueError(
                f"Invalid application name: {self.configuration.app_name}"
            )

        info("Configuration validated successfully.")

        return True

    def get_configuration(self) -> DjangoConfiguration:
        """
        Return validated configuration.
        """

        self.validate()

        return self.configuration