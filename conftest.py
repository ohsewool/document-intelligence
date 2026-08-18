"""Make the package importable without environment setup.

The suite previously required PYTHONPATH to be set by hand, so a fresh checkout
collected zero tests and reported success.
"""

import sys
from pathlib import Path

source = Path(__file__).resolve().parent / "src"
if source.exists():
    sys.path.insert(0, str(source))
