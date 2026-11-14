"""
------------------------------------------------------------
File: commands.py

Module: CLI

Purpose:
Register and execute all AP Studio CLI commands.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

from typing import Callable
from pathlib import Path

from source.core.generator.project_generator import ProjectGenerator
from source.core.logger.logger import info, success, error


class CommandRegistry:
    """
    Stores and manages all CLI commands.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("create", self.handle_create)

    def register(self, command_name: str, handler: Callable) -> None:
        """
        Register a new command.
        """
        self._commands[command_name] = handler

    def execute(self, command_name: str, *args, **kwargs) -> None:
        """
        Execute a registered command.
        """
        command = self._commands.get(command_name)
        if command is None:
            error(f"Unknown command: {command_name}")
            return
        command(*args, **kwargs)

    def list_commands(self) -> list[str]:
        """
        Return all available command names.
        """
        return sorted(self._commands.keys())

    @staticmethod
    def handle_create(args) -> None:
        """
        Handle 'aps create <project_name>' execution.
        """
        project_name = getattr(args, "project_name", "").strip()
        app_name = getattr(args, "app", "main").strip()
        target_dir = getattr(args, "dir", ".").strip()

        if not project_name:
            error("Project name cannot be empty.")
            return

        generator = ProjectGenerator(
            project_name=project_name,
            app_name=app_name,
            target_dir=Path(target_dir),
        )

        ok = generator.create()
        if ok:
            print("\n" + "=" * 55)
            print("🎉 AP Studio Project Ready!")
            print("=" * 55)
            print("To start your development server:")
            print(f"  cd {project_name}")
            print("  python manage.py runserver")
            print("=" * 55 + "\n")
