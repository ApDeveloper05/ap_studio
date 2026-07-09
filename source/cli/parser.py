"""
AP Studio CLI Argument Parser
"""

from argparse import ArgumentParser

from source.cli.version import APP_NAME, VERSION


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="aps",
        description="AP Studio Command Line Interface",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{APP_NAME} v{VERSION}",
    )

    return parser