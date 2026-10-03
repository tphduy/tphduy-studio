#!/usr/bin/env python3
"""Check repository conventions and invoke Claude's native validator."""

from pathlib import Path
import shutil  # noqa: F401  re-exported so tests can patch verify.shutil
import subprocess  # noqa: F401  re-exported so tests can patch verify.subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verifier import Verifier  # noqa: E402
from verifier.cli import main  # noqa: E402

__all__ = ["Verifier", "main", "shutil", "subprocess"]

if __name__ == "__main__":
    sys.exit(main())
