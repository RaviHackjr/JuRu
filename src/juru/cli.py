#!/usr/bin/env python3
"""JuRu CLI — just like python file.py, plus templates and a REPL.

    python3 juru.py program.jr        run a program
    python3 juru.py --new NAME        start NAME.jr from the starter template
    python3 juru.py --new NAME TPL    start NAME.jr from a chosen template
    python3 juru.py --templates       list every template
    python3 juru.py repl              open the live REPL
    python3 juru.py --version         print the version

Installed as a package, the same commands are available as `juru ...`.

The full pipeline, all connected:
    .jr file → lexer → parser → checker → interpreter → output

JuRu files use the extension: .jr
"""

import os
import re
import sys

from .lexer import JuRuGalti
from .parser import parse_source
from .checker import Checker, did_you_mean
from .interpreter import Interpreter
from .version import VERSION
from .errfmt import render

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(HERE, "templates")

# template name → one-line description (kept in sync with templates/*.jr)
TEMPLATES = {
    "starter": "the smallest useful program: variables, loops, lists",
    "calculator": "a tiny talking calculator — while + split + float + int",
    "quiz": "three questions, one score — lists + ask",
    "guessing_game": "guess the secret number — random + while",
    "word_stats": "read a sentence like a search engine — split + count + sorted",
}

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

USAGE = """JuRu {} — the easy, secure programming language

  python3 juru.py program.jr        run a program
  python3 juru.py --new NAME        start NAME.jr from the starter template
  python3 juru.py --new NAME TPL    start NAME.jr from a chosen template
  python3 juru.py --templates       list every template
  python3 juru.py repl              open the live REPL
  python3 juru.py --version         print the version""".format(VERSION)


def fail(message):
    print(message)
    sys.exit(1)


def list_templates():
    width = max(len(name) for name in TEMPLATES)
    print("JuRu templates — start one with: python3 juru.py --new NAME TEMPLATE")
    for name, description in TEMPLATES.items():
        print("  {}  {}".format(name.ljust(width), description))


def do_new(args):
    if len(args) < 1 or len(args) > 2:
        fail("who should I create?  python3 juru.py --new NAME [template]")
    name, template = args[0], (args[1] if len(args) == 2 else "starter")
    if not NAME_RE.match(name):
        fail("'{}' is not a usable program name — "
             "use letters, digits and _ (starting with a letter)".format(name))
    target = name + ".jr"
    if os.path.exists(target):
        fail("'{}' already exists — pick another name (I never overwrite)".format(target))
    if template not in TEMPLATES:
        close = did_you_mean(template, list(TEMPLATES))
        head = "no template '{}'".format(template)
        if close:
            head += " — did you mean '{}'?".format(close)
        head += " — the templates are: " + ", ".join(TEMPLATES)
        fail(head)
    source = os.path.join(TEMPLATES_DIR, template + ".jr")
    try:
        with open(source, encoding="utf-8") as f:
            text = f.read()
        with open(target, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as err:
        fail("could not create '{}' — {}".format(target, err))
    print("created {} from the '{}' template".format(target, template))
    print("run it:  python3 juru.py {}".format(target))


def run_program(path):
    if not path.endswith(".jr"):
        fail("JuRu files end with '.jr' — you gave: '{}'".format(path))
    if not os.path.exists(path):
        fail("file not found: '{}'".format(path))
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        tree = parse_source(src)
        Checker().check(tree)   # semantic checks before a single line runs
    except JuRuGalti as err:
        fail(render(err, src))
    try:
        base = os.path.dirname(os.path.abspath(path))
        Interpreter().run(tree, base_dir=base)   # imports resolve next to the file
    except JuRuGalti as err:
        fail(render(err, src))
    except (RecursionError, MemoryError):
        fail("JuRu Error: this program used too much of something — "
             "deep recursion or a value that grew too big")
    except Exception as err:                     # never show a Python traceback
        fail("JuRu Error: something broke inside JuRu itself (a bug, not your fault)\n"
             "       please report it — details: {}: {}".format(type(err).__name__, err))


def run_repl():
    from .repl import main as repl_main
    repl_main()


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        run_repl()          # like typing `python` with no arguments
        return
    first = args[0]
    if first in ("--help", "-h"):
        print(USAGE)
    elif first == "--version":
        print("JuRu " + VERSION)
    elif first == "--templates":
        list_templates()
    elif first == "--new":
        do_new(args[1:])
    elif first == "repl":
        run_repl()
    elif first.startswith("--"):
        fail("I do not know '{}' — try python3 juru.py --help".format(first))
    elif len(args) != 1:
        fail("one program at a time — try python3 juru.py --help")
    else:
        run_program(first)


if __name__ == "__main__":
    main()
