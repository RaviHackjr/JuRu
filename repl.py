#!/usr/bin/env python3
"""JuRu REPL launcher — the real REPL lives in the src/juru/ package.

    python3 repl.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from juru.repl import main  # noqa: E402

if __name__ == "__main__":
    main()
