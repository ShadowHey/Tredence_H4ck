#!/usr/bin/env python3
"""Convenience script to run ShelfSense AI image parsing on sample inputs."""

import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from shelf_image_parsing.cli import main

if __name__ == "__main__":
    # If no arguments provided, default to sample_inputs -> outputs
    if len(sys.argv) == 1:
        sys.argv.extend([
            "--input", str(PROJECT_ROOT / "sample_inputs"),
            "--output", str(PROJECT_ROOT / "outputs"),
            "--save-json",
            "--save-csv",
        ])
    sys.exit(main())
