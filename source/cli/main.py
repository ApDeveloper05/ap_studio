"""
AP Studio CLI Entry Point
"""

import sys
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
    args = parser.parse_args()

    command_registry = CommandRegistry()

    if args.command:
        banner()
        command_registry.execute(args.command, args)
    else:
        banner()
        parser.print_help()


if __name__ == "__main__":
    main()
