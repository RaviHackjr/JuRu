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

from .lexer import JuRuGalti
from .parser import (
    Node, Name, Assign, Call, For, FuncDef, Import, Member,
    parse_source,
)
from .stdlib import BUILTINS, BUILTIN_ARITY, BUILTIN_HINT, check_arity


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
            bad = check_arity(name, count)
            if bad is not None:
                raise JuRuGalti(n.line, n.col, bad)
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
