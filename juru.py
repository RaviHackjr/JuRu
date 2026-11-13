#!/usr/bin/env python3
"""JuRu runner — just like python file.py:  python3 juru.py program.jr

The full pipeline, all connected:
    .jr file → lexer → parser → checker (Step 3) → interpreter → output

JuRu files use the extension: .jr
"""

import os
import sys

from lexer import JuRuGalti
from parser import parse_source
from checker import Checker
from interpreter import Interpreter


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 juru.py program.jr")
        sys.exit(1)
    path = sys.argv[1]
    if not path.endswith(".jr"):
        print("JuRu files end with '.jr' — you gave: '{}'".format(path))
        sys.exit(1)
    if not os.path.exists(path):
        print("File not found: '{}'".format(path))
        sys.exit(1)
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        tree = parse_source(src)
        Checker().check(tree)   # Step 3: semantic checks before a single line runs
    except JuRuGalti as err:
        print(str(err))
        sys.exit(1)
    try:
        base = os.path.dirname(os.path.abspath(path))
        Interpreter().run(tree, base_dir=base)   # imports resolve next to the file
    except JuRuGalti as err:
        print(str(err))
        sys.exit(1)
    except (RecursionError, MemoryError) as err:
        print("JuRu Error: this program used too much of something — "
              "deep recursion or a value that grew too big")
        sys.exit(1)
    except Exception as err:                     # never show a Python traceback
        print("JuRu Error: something broke inside JuRu itself (a bug, not your fault)\n"
              "       please report it — details: {}: {}".format(type(err).__name__, err))
        sys.exit(1)


if __name__ == "__main__":
    main()
