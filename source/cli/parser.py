"""
AP Studio CLI Argument Parser
"""

from argparse import ArgumentParser

from source.cli.version import APP_NAME, VERSION


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="aps",
        description=f"{APP_NAME} - Enterprise Scaffolder & Authentication Engine",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{APP_NAME} v{VERSION}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
    )

    # aps create <project_name>
    create_subparser = subparsers.add_parser(
        "create",
        help="Create and scaffold a new Django project with pre-configured auth",
    )

    create_subparser.add_argument(
        "project_name",
        type=str,
        help="Name of the new project (e.g. myproject)",
    )

    create_subparser.add_argument(
        "-a",
        "--app",
        type=str,
        default="main",
        help="Name of the main domain app to generate (default: main)",
    )

    create_subparser.add_argument(
        "-d",
        "--dir",
        type=str,
        default=".",
        help="Target parent directory to create project in (default: current directory)",
    )

    return parser
