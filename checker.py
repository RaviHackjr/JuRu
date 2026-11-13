"""JuRu Language — Step 3: Semantic Checker (AST → is this program sound?)
==========================================================================

JuRu = easy + secure language.

The checker sits BETWEEN the parser and the interpreter:

    lexer → parser → CHECKER → interpreter
                     (juru.py wires them together)

It catches semantic mistakes BEFORE a single line runs:
- reading a name that is never assigned anywhere (typos die here)
- assigning to a reserved builtin (ask / len / int / upper / lower / str / push / sum / min / max)
- a func that repeats the same parameter
- calling a func with the wrong number of arguments
  (builtins always; user funcs when the definition is unambiguous)
- calling a name that is never defined anywhere

Policy: be CONSERVATIVE — never flag a program that could run.
If a name is assigned somewhere in the program, the checker allows it;
the interpreter (step 4) still guards the actual run order at runtime.

How to run:
    python3 checker.py file.jr   # print OK, or the first semantic error
"""

import difflib

from lexer import JuRuGalti
from parser import (
    Node, Name, Assign, Call, For, FuncDef, Import, Member,
    parse_source,
)

# same reserved names as the interpreter (kept independent on purpose)
BUILTINS = ("ask", "len", "int", "upper", "lower", "str", "push", "sum", "min", "max",
            "split", "join", "trim", "replace", "abs", "round", "random", "sqrt",
            "sorted", "reverse", "find", "keys", "values", "count")

# (min_args, max_args) for every builtin — checked before a single line runs
BUILTIN_ARITY = {
    "ask": (0, 1),
    "len": (1, 1),
    "int": (1, 1),
    "upper": (1, 1),
    "lower": (1, 1),
    "str": (1, 1),
    "push": (2, 2),
    "sum": (1, 1),
    "min": (2, 2),
    "max": (2, 2),
    "split": (2, 2),
    "join": (2, 2),
    "trim": (1, 1),
    "replace": (3, 3),
    "abs": (1, 1),
    "round": (1, 1),
    "random": (2, 2),
    "sqrt": (1, 1),
    "sorted": (1, 1),
    "reverse": (1, 1),
    "find": (2, 2),
    "keys": (1, 1),
    "values": (1, 1),
    "count": (2, 2),
}

# the exact message the interpreter would print — both layers say the same thing
BUILTIN_HINT = {
    "ask": "ask(prompt) takes at most 1 argument",
    "len": "len(x) takes exactly 1 argument",
    "int": "int(x) takes exactly 1 argument",
    "upper": "upper(x) takes exactly 1 argument",
    "lower": "lower(x) takes exactly 1 argument",
    "str": "str(x) takes exactly 1 argument",
    "push": "push(list, item) takes exactly 2 arguments",
    "sum": "sum(list) takes exactly 1 argument",
    "min": "min(a, b) takes exactly 2 arguments",
    "max": "max(a, b) takes exactly 2 arguments",
    "split": "split(text, separator) takes exactly 2 arguments",
    "join": "join(list, separator) takes exactly 2 arguments",
    "trim": "trim(x) takes exactly 1 argument",
    "replace": "replace(text, old, new) takes exactly 3 arguments",
    "abs": "abs(x) takes exactly 1 argument",
    "round": "round(x) takes exactly 1 argument",
    "random": "random(low, high) takes exactly 2 arguments",
    "sqrt": "sqrt(x) takes exactly 1 argument",
    "sorted": "sorted(list) takes exactly 1 argument",
    "reverse": "reverse(list) takes exactly 1 argument",
    "find": "find(list, item) takes exactly 2 arguments",
    "keys": "keys(dict) takes exactly 1 argument",
    "values": "values(dict) takes exactly 1 argument",
    "count": "count(list, item) takes exactly 2 arguments",
}


def did_you_mean(name, candidates):
    """The closest known name for a typo — None when nothing is close."""
    if not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None


class Checker:
    """One check() call = the whole program must be semantically sound."""

    def check(self, program, known_env=None):
        self.assigned = set(BUILTINS)   # every name that ever gets a value
        self.funcs = {}                 # func name → list of param counts
        if known_env is not None:       # REPL: names from earlier lines stay valid
            self._seed(known_env)
        self._collect(program)
        self._validate(program)
        return program

    def _seed(self, env):
        """Names (and funcs) that already live in a live environment."""
        e = env
        while e is not None:
            for name, value in e.vars.items():
                self.assigned.add(name)
                if hasattr(value, "params"):    # duck-typed FuncValue
                    self.funcs.setdefault(name, []).append(len(value.params))
            e = e.parent

    # ---------- traversal ----------

    def _walk(self, node):
        """Yield every AST node (parents first, then children)."""
        yield node
        for field in node._fields:
            val = getattr(node, field)
            if isinstance(val, Node):
                yield from self._walk(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, Node):
                        yield from self._walk(item)

    # ---------- pass 1: collect every declaration ----------

    def _collect(self, program):
        for n in self._walk(program):
            if isinstance(n, Assign):
                self.assigned.add(n.name)
            elif isinstance(n, FuncDef):
                self.assigned.add(n.name)
                self.assigned.update(n.params)
                self.funcs.setdefault(n.name, []).append(len(n.params))
            elif isinstance(n, For):
                self.assigned.add(n.var)
            elif isinstance(n, Import):
                self.assigned.add(n.module)

    # ---------- pass 2: validate every use ----------

    def _validate(self, program):
        for n in self._walk(program):
            if isinstance(n, Name):
                if n.id not in self.assigned:
                    raise JuRuGalti(n.line, n.col, self._not_found_msg(n.id))
            elif isinstance(n, Assign):
                if n.name in BUILTINS:
                    raise JuRuGalti(
                        n.line, n.col,
                        "'{}' is reserved (builtin) — pick another name".format(n.name))
            elif isinstance(n, FuncDef):
                self._check_funcdef(n)
            elif isinstance(n, Import):
                if n.module in BUILTINS:
                    raise JuRuGalti(
                        n.line, n.col,
                        "the file '{}' would create the module '{}' — that name "
                        "is a reserved builtin; rename the file".format(n.path, n.module))
            elif isinstance(n, Call):
                self._check_call(n)

    def _check_funcdef(self, n):
        if n.name in BUILTINS:
            raise JuRuGalti(n.line, n.col,
                            "'{}' is reserved (builtin) — pick another name".format(n.name))
        seen = set()
        for p in n.params:
            if p in seen:
                raise JuRuGalti(
                    n.line, n.col,
                    "func '{}' has the parameter '{}' twice — "
                    "give every parameter its own name".format(n.name, p))
            seen.add(p)

    def _not_found_msg(self, name):
        """The full 'was not found' message, with the best hint available."""
        if name in ("dikhao", "bolo"):
            return "'{}' was not found (the old 'bolo' is now 'say')".format(name)
        close = did_you_mean(name, self.assigned)
        if close:
            return "'{}' was not found — did you mean '{}'? (nothing with this name is ever assigned)".format(name, close)
        return "'{}' was not found (nothing with this name is ever assigned)".format(name)

    def _check_call(self, n):
        if n.callee is not None:
            # utils.double(4) — we cannot see inside the module without
            # running it, so be conservative: only the base name must exist
            base = n.callee
            while isinstance(base, Member):
                base = base.seq
            if isinstance(base, Name) and base.id not in self.assigned:
                raise JuRuGalti(base.line, base.col, self._not_found_msg(base.id))
            return
        name, count = n.name, len(n.args)
        if name in BUILTIN_ARITY:
            low, high = BUILTIN_ARITY[name]
            if count < low or count > high:
                raise JuRuGalti(n.line, n.col, BUILTIN_HINT[name])
            return
        if name in self.funcs:
            counts = self.funcs[name]
            if len(counts) == 1 and count != counts[0]:
                word = "argument" if counts[0] == 1 else "arguments"
                raise JuRuGalti(
                    n.line, n.col,
                    "func '{}' expects {} {}, you gave {}".format(
                        name, counts[0], word, count))
            return
        if name not in self.assigned:
            raise JuRuGalti(n.line, n.col, self._not_found_msg(name))


# ------------------------------------------------------------------ helpers

def check_source(src):
    """Text → parse → semantic check. Returns the AST when sound."""
    tree = parse_source(src)
    Checker().check(tree)
    return tree


def check_file(path):
    with open(path, encoding="utf-8") as f:
        return check_source(f.read())


def _run_cli():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 checker.py file.jr")
        sys.exit(1)
    try:
        check_file(sys.argv[1])
    except JuRuGalti as err:
        print(str(err))
        sys.exit(1)
    print("OK — no semantic errors ✅")


if __name__ == "__main__":
    _run_cli()
