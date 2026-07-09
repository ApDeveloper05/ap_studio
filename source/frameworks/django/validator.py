"""
------------------------------------------------------------
File: validator.py

Module: Django Framework

Purpose:
Validate the local development environment before
installing or creating a Django project.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import shutil
import subprocess

from source.core.logger.logger import info


class DjangoValidator:
    """
    Validate Django development requirements.
    """

    @staticmethod
    def is_python_installed() -> bool:
        """
        Check whether Python is installed.
        """

        return shutil.which("python") is not None

    @staticmethod
    def is_pip_installed() -> bool:
        """
        Check whether pip is installed.
        """

        return shutil.which("pip") is not None

    @staticmethod
    def is_django_installed() -> bool:
        """
        Check whether Django is installed.
        """

        try:
            subprocess.run(
                ["python", "-m", "django", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return True

        except Exception:
            return False

    @staticmethod
    def get_django_version() -> str | None:
        """
        Return installed Django version.
        """

        try:
            result = subprocess.run(
                ["python", "-m", "django", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout.strip()

        except Exception:
            return None

    def validate(self) -> bool:
        """
        Validate the development environment.
        """

        info("Validating Django environment...")

        if not self.is_python_installed():
            info("Python not found.")
            return False

        if not self.is_pip_installed():
            info("pip not found.")
            return False

        if not self.is_django_installed():
            info("Django not installed.")
            return False

        info(
            f"Django {self.get_django_version()} detected successfully."
        )

        return True