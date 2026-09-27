#!/usr/bin/env python3
"""Raccourci historique : équivaut à `python3 -m solfege` (code dans solfege/)."""

import sys

from solfege.cli import main

if __name__ == "__main__":
    sys.exit(main())
