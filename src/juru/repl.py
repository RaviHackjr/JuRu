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
"""

from .lexer import JuRuGalti, Lexer, KEYWORD, OPERATOR, NEWLINE, EOF
from .parser import parse_source, ExprSt, Call
from .checker import Checker
from .interpreter import Interpreter, Env, display
from .version import VERSION
from .helpdb import overview
from .errfmt import render

BANNER = ("JuRu {} REPL — full English, easy like Python, secure like Rust.\n"
          "type 'exit' or press Ctrl-D to leave\n"
          "type 'cancel' or press Ctrl-C to drop an open block\n"
          "type help() to see the whole toolbox").format(VERSION)
PROMPT = "jruru> "
CONT_PROMPT = "......> "

# a line (or block so far) that ends with one of these wants MORE input
CONTINUE_OPS = {"+", "-", "*", "/", "%", ",", "=",
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
