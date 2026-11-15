#!/usr/bin/env python3
"""PyInstaller entry point — builds the standalone `juru` interpreter.

PyInstaller freezes the src/juru package into a single executable, so
people can run JuRu without installing Python at all:

    python3 -m PyInstaller juru.spec     # produces dist/juru (or juru.exe)

The root launchers (juru.py, repl.py, checker.py) stay exactly as they
are — this file exists only for the frozen build.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
