#!/usr/bin/env python3
"""JuRu REPL — the language, one block at a time.

Run it:  python3 repl.py

Every entry is parsed, checked (step 3) and run (step 4) against the SAME
environment, so names and funcs survive from line to line.

- a lone expression echoes its value:      1 + 2        -> => 3
- say(...) prints directly, no echo:       say("hi")    -> hi
- a block may span lines:                  for i from 1 to 2 {
                                               say(i)
                                           }
- a line that ends mid-thought (an operator or an open bracket) keeps going
- made a mistake in an open block? type 'cancel' (or press Ctrl-C)
- mistakes print a friendly error and the session goes on
- type exit (or press Ctrl-D) to leave
- a terminal command typed here by mistake (juru --version, pip, dir...)
  gets a one-line nudge — what this is, and where to run it — never a
  "'juru' was not found" error
"""

import sys

from .lexer import JuRuGalti, Lexer, KEYWORD, OPERATOR, NEWLINE, EOF
from .parser import parse_source, ExprSt, Call
from .checker import Checker
from .interpreter import Interpreter, Env, display
from .version import VERSION
from .helpdb import overview
from .errfmt import render

# The banner reads like Python's: version + build note + platform on the
# first line, then the "Type ..." hint line, then the JuRu one-liner.
# sys.platform says win32 / linux / darwin — the same words Python uses.
BANNER = ("JuRu {} (easy like Python, secure like Rust) on {}\n"
          "Type \"help\", \"exit\" or \"cancel\" for more information.\n"
          "type help() to see the whole toolbox").format(VERSION, sys.platform)
PROMPT = "juru> "
CONT_PROMPT = "....> "

# a line (or block so far) that ends with one of these wants MORE input
CONTINUE_OPS = {"+", "-", "*", "/", "%", ",", "=",
                "+=", "-=", "*=", "/=", "%=",
                "==", "!=", "<", "<=", ">", ">=", "(", "[", "{"}
CONTINUE_KWS = {"and", "or", "not", "from", "to", "in", "import", "else"}


def is_say_expr(st):
    """say(...) prints on its own — it must not echo."""
    return isinstance(st, ExprSt) and isinstance(st.expr, Call) and st.expr.name == "say"


def looks_incomplete(src):
    """True when the text so far cannot end here — more lines are needed."""
    try:
        toks = Lexer(src).tokenize()
    except JuRuGalti:
        return True               # half-typed text (an unclosed " for example)
    braces = parens = brackets = 0
    for t in toks:
        if t.type == OPERATOR:
            if t.value == "{":
                braces += 1
            elif t.value == "}":
                braces -= 1
            elif t.value == "(":
                parens += 1
            elif t.value == ")":
                parens -= 1
            elif t.value == "[":
                brackets += 1
            elif t.value == "]":
                brackets -= 1
    if braces > 0 or parens > 0 or brackets > 0:
        return True
    meaningful = [t for t in toks if t.type not in (NEWLINE, EOF)]
    if not meaningful:
        return False
    last = meaningful[-1]
    if last.type == OPERATOR and last.value in CONTINUE_OPS:
        return True
    if last.type == KEYWORD and last.value in CONTINUE_KWS:
        return True
    return False


# Terminal commands people paste into the REPL by mistake. They get a
# nudge in one line — never a "'juru' was not found" error. Names that a
# real JuRu program could use (juru = 5, juru + 3) still work as code.
TERMINAL_ALWAYS = {"pip", "pip3", "dir", "cls", "ls", "cd", "cat", "echo"}
TERMINAL_FIRST = TERMINAL_ALWAYS | {"juru", "jruru", "python", "python3"}


def is_terminal_wish(text):
    """True when a line is a terminal command, not JuRu code."""
    if text.startswith("--"):
        return True                     # --version, --new, --help...
    first = text.split(" ", 1)[0]
    if first not in TERMINAL_FIRST:
        return False
    rest = text[len(first):].lstrip()
    if not rest:
        return first in TERMINAL_ALWAYS  # bare `pip`, `dir`...
    if rest[0] in "=+*/%<>!:" or rest[0] == "(":
        return False                     # `juru = 5`, `juru(x)`, `juru + 3`
    if rest[0] == "-" and rest[1:2] == " ":
        return False                     # `juru - 3` is subtraction
    return True                          # `juru --version`, `juru hello.jr`


def terminal_reply(text):
    """The one-line nudge for a terminal command typed in the REPL."""
    if text.split(" ", 1)[0] in ("pip", "pip3"):
        return ("JuRu needs no pip — the whole toolbox is already built in "
                "(type help() to see it)")
    return ("this is the JuRu REPL, not the terminal — type exit first, "
            "then run \"{}\" in your terminal").format(text)


def run_line(interp, env, text):
    """One REPL entry -> (env, echo-or-None). Raises JuRuGalti on mistakes."""
    tree = parse_source(text)
    Checker().check(tree, env)          # step 3 sees the names of earlier lines
    if len(tree.stmts) == 1 and isinstance(tree.stmts[0], ExprSt) \
            and not is_say_expr(tree.stmts[0]):
        value = interp.eval(tree.stmts[0].expr, env)
        return env, "=> " + display(value)
    interp.run(tree, env)               # step 4
    return env, None


def main():
    print(BANNER)
    interp = Interpreter()
    env = Env()
    pending = ""
    while True:
        try:
            line = input(CONT_PROMPT if pending else PROMPT)
        except EOFError:                # Ctrl-D
            print()
            if pending:
                print("JuRu Error: the block is not closed — '}' is missing")
                pending = ""
                continue
            break
        except KeyboardInterrupt:       # Ctrl-C drops whatever was being typed
            print()
            pending = ""
            continue
        if pending:
            if line.strip() == "cancel":    # drop the open block, start over
                pending = ""
                continue
            text = pending + "\n" + line
        else:
            text = line.strip()
            if text in ("exit", "quit"):
                break
            if text in ("help", "?"):
                print(overview())          # bare help, no parens needed
                continue
            if not text:
                continue
            if is_terminal_wish(text):     # a terminal command pasted here
                print(terminal_reply(text))
                continue
        if looks_incomplete(text):
            pending = text
            continue
        pending = ""
        try:
            env, echo = run_line(interp, env, text)
            if echo is not None:
                print(echo)
        except JuRuGalti as err:
            print(render(err, text))
        except RecursionError:
            print("JuRu Error: recursion went too deep — it never stops")
        except MemoryError:
            print("JuRu Error: that value grew too big — try a smaller one")
        except Exception as err:                 # never show a Python traceback
            print("JuRu Error: something broke inside JuRu itself (a bug, not your fault)\n"
                  "       please report it — details: {}: {}".format(type(err).__name__, err))


if __name__ == "__main__":
    main()
