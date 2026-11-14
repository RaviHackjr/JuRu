#!/usr/bin/env python3
"""JuRu checker launcher — the real checker lives in the src/juru/ package.

    python3 checker.py file.jr   # print OK, or the first semantic error
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from juru.checker import _run_cli  # noqa: E402

if __name__ == "__main__":
    _run_cli()
