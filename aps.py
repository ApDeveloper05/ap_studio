#!/usr/bin/env python
"""
------------------------------------------------------------
File: aps.py

Module: AP Studio CLI Root Runner

Purpose:
Convenient root entrypoint for AP Studio Command Line Interface.
Allows running:
  python aps.py create myproject
  python aps.py --version

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from source.cli.main import main

if __name__ == "__main__":
    main()
