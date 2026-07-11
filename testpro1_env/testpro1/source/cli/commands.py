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


class CommandRegistry:
    """
    Stores and manages all CLI commands.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Callable] = {}

    def register(self, command_name: str, handler: Callable) -> None:
        """
        Register a new command.
        """

        self._commands[command_name] = handler

    def execute(self, command_name: str) -> None:
        """
        Execute a registered command.
        """

        command = self._commands.get(command_name)

        if command is None:
            print(f"Unknown command: {command_name}")
            return

        command()

    def list_commands(self) -> list[str]:
        """
        Return all available command names.
        """

        return sorted(self._commands.keys())