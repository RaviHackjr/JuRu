#!/usr/bin/env python3
"""PyInstaller entry point — builds the standalone `juru` interpreter.

PyInstaller freezes the src/juru package into a single executable, so
people can run JuRu without installing Python at all:

    python3 -m PyInstaller juru.spec     # produces dist/juru (or juru.exe)

This file lives in packaging/ (not the repo root) on purpose: PyInstaller
searches the entry script's own directory first, and a module named
`juru` on that path would shadow the real src/juru package.

The root launchers (juru.py, repl.py, checker.py) stay exactly as they
are — this file exists only for the frozen build.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from juru.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
