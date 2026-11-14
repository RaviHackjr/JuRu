#!/usr/bin/env python3
"""JuRu launcher — the real code lives in the src/juru/ package.

    python3 juru.py program.jr        run a program
    python3 juru.py --new NAME [TPL]  start from a template
    python3 juru.py repl              open the live REPL
    python3 juru.py --version

Installed with pip, the same commands are simply `juru ...`.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from juru.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
