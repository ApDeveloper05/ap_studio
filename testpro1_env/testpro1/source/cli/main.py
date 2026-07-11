"""
AP Studio CLI Entry Point
"""

from source.cli.parser import create_parser
from source.cli.commands import CommandRegistry
from source.cli.version import (
    APP_NAME,
    VERSION,
    STATUS,
    AUTHOR,
)


def banner() -> None:
    print("=" * 55)
    print(f"🚀 {APP_NAME}")
    print("=" * 55)
    print(f"Version : {VERSION}")
    print(f"Status  : {STATUS}")
    print(f"Author  : {AUTHOR}")
    print("=" * 55)


def main() -> None:
    parser = create_parser()
    parser.parse_args()
    command_registry = CommandRegistry()
    banner()


if __name__ == "__main__":
    main()