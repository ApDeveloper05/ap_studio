"""
------------------------------------------------------------
File: installer.py

Module: Django Framework

Purpose:
Install and prepare the Django development environment.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import subprocess

from source.core.logger.logger import error
from source.core.logger.logger import info
from source.frameworks.django.validator import DjangoValidator


class DjangoInstaller:
    """
    Handles Django installation.
    """

    def __init__(self) -> None:
        self.validator = DjangoValidator()

    def install(self) -> bool:
        """
        Install Django if it is not available.
        """

        info("Checking Django installation...")

        if not self.validator.is_python_installed():
            error("Python is not installed.")
            return False

        if not self.validator.is_pip_installed():
            error("pip is not installed.")
            return False

        if self.validator.is_django_installed():

            version = self.validator.get_django_version()

            info(f"Django {version} is already installed.")

            return True

        info("Installing Django...")

        try:

            subprocess.run(
                [
                    "python",
                    "-m",
                    "pip",
                    "install",
                    "django",
                ],
                check=True,
            )

            version = self.validator.get_django_version()

            info(f"Django {version} installed successfully.")

            return True

        except subprocess.CalledProcessError:

            error("Failed to install Django.")

            return False