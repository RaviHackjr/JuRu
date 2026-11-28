"""JuRu Language — Step 4: Interpreter (AST → a running program)
================================================================

JuRu = easy + secure language.

A tree-walking interpreter: it runs the parser's AST.

Design rules:
- int/float automatic (like Python): 10 / 4 = 2.5, 1 + 2.5 = 3.5
- text + anything = text ("Level " + 3 → "Level 3") — friendly
- list indexing is always bounds-checked (security)
- and/or short-circuit (safe)
- a loop running over 10,000,000 times? it stops (runaway protection)
- every mistake gets a human error message with line/col

How to run:
    python3 juru.py program.jr
"""

import builtins
import json
import math
import os
import random as _random
import time
import unicodedata

from .lexer import JuRuGalti
from .parser import (
    Program, Num, Text, Bool, Null, Name, ListLit, DictLit, BinOp, UnaryOp,
    Call, Index, Member, Assign, SetIndex, ExprSt, Say, If, While, For,
    FuncDef, Return, Import, Break, Continue, TrySt,
    parse_source,
)
from .checker import check_source, did_you_mean
from .helpdb import overview, card_for, unknown
from .stdlib import BUILTINS, check_arity
MAX_LOOP_STEPS = 10_000_000        # runaway loop protection


class FuncValue:
    __slots__ = ("name", "params", "body", "env")

    def __init__(self, name, params, body, env):
        self.name = name
        self.params = params
        self.body = body
        self.env = env


class ModuleValue:
    """One imported file: its name, its own env, where it lives."""

    __slots__ = ("name", "env", "path")

    def __init__(self, name, env, path):
        self.name = name
        self.env = env
        self.path = path


class SetV:
    """A JuRu set — a bag of values with no duplicates, in first-seen order.

    Backed by a plain list (not Python's set) so equality stays exactly
    JuRu's equality — true != 1, but 1 == 1.0 — and lists can ride along.
    A set is born from set_of([...]); {} is a dict, forever.
    """

    __slots__ = ("items",)

    def __init__(self, items=()):
        self.items = []
        for x in items:
            self.add(x)

    def add(self, x):
        if not any(_same_value(x, y) for y in self.items):
            self.items.append(x)

    def has(self, x):
        return any(_same_value(x, y) for y in self.items)

    def __len__(self):
        return len(self.items)


class ErrV:
    """A JuRu error value — the caught error, usable inside rescue.

    Built from the raised JuRuGalti; exposes exactly four fields
    (e.message, e.line, e.col, e.kind). The recorded call stack stays
    display-only — it is shown by errfmt's "called from" lines and is
    never part of the value.
    """

    __slots__ = ("message", "line", "col", "kind")

    def __init__(self, err):
        self.message = err.message
        self.line = err.line
        self.col = err.col
        self.kind = getattr(err, "kind", None) or "type"

    def __repr__(self):
        return "<error {}: {}>".format(self.kind, self.message)


def _same_value(a, b):
    """The ONE equality rule for the whole language: ==, find, count,
    unique and sets all share it. true != 1 (different categories),
    but 1 == 1.0 (same number family)."""
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if _is_num(a) and _is_num(b):
        return a == b
    if isinstance(a, SetV) and isinstance(b, SetV):
        if len(a.items) != len(b.items):
            return False
        return all(any(_same_value(x, y) for y in b.items) for x in a.items)
    if isinstance(a, ErrV) and isinstance(b, ErrV):
        return (a.message == b.message and a.kind == b.kind
                and a.line == b.line and a.col == b.col)
    if type(a) is not type(b):
        return False
    return a == b


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Env:
    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent


def _typename(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "dict"
    if isinstance(v, SetV):
        return "set"
    if isinstance(v, ErrV):
        return "error"
    if isinstance(v, FuncValue):
        return "func"
    if isinstance(v, ModuleValue):
        return "module"
    return type(v).__name__


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _truthy(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (str, list, dict)):
        return len(v) > 0
    if isinstance(v, SetV):
        return len(v.items) > 0
    return True


def display(v):
    """Turn a value into text people can read (for say)."""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + ", ".join(display(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(
            display(k) + ": " + display(x) for k, x in v.items()) + "}"
    if isinstance(v, SetV):
        if not v.items:
            return "set()"
        return "{" + ", ".join(display(x) for x in v.items) + "}"
    if isinstance(v, ErrV):
        return "<error {}: {}>".format(v.kind, v.message)
    if isinstance(v, str):
        return v
    if isinstance(v, FuncValue):
        return "<func {}>".format(v.name)
    if isinstance(v, ModuleValue):
        return "<module {}>".format(v.name)
    return str(v)


def _char_width(ch):
    """The display width of ONE character (the padding policy, pinned).

    A consistent approximation of terminal columns: combining marks and
    other zero-width characters count 0, East Asian wide/fullwidth
    characters count 2, everything else counts 1. len() keeps counting
    CHARACTERS — padding is the only place that thinks in columns.
    """
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def _display_width(text):
    """The display width of a piece of text, under _char_width's policy."""
    return sum(_char_width(ch) for ch in text)


def _count_word(n, word):
    """1 value / 2 values — plain English counts in error messages."""
    return "{} {}".format(n, word if n == 1 else word + "s")


def _lines_from_text(text):
    """split_lines()'s rule, shared with read_lines().

    Splits on \\n, \\r\\n and a lone \\r. An empty text has NO lines; a
    trailing newline opens no extra empty line; blank lines are kept.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text == "":
        return []
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _has_lone_surrogate(text):
    """True when text holds half of a surrogate pair (utf-8 cannot show it)."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return True
    return False


def _format_text(template, values, line, col):
    """format()'s engine — slots only, never expressions.

    The template is scanned once, left to right:
      {}       the next value, left to right (automatic mode)
      {0}      the value at that zero-based index (may repeat)
      {{ / }}  a literal { or }
    Anything else between braces ({x}, { 0 }, {-1}) is a friendly error,
    and so is a lone brace. The two slot styles never mix. Numbered
    slots may skip: values fill positions 0 … highest index, so
    {0} and {2} with three values is fine — but values beyond the
    highest referenced index are an error (a typo should not vanish).
    Values render with the exact same rules as str() / say(). No eval,
    no expression embedding — format() formats values, not code.
    """
    pieces = []      # text pieces; None marks an automatic slot, int a numbered one
    autos = 0        # how many {} slots the text has
    numbered = []    # every explicit {0}-style index, in text order

    i = 0
    n = len(template)
    while i < n:
        ch = template[i]
        if ch == "{":
            if i + 1 < n and template[i + 1] == "{":
                pieces.append("{")
                i += 2
                continue
            close = template.find("}", i + 1)
            if close < 0:
                raise JuRuGalti(line, col,
                                "format() found a lone '{' — write '{{' for "
                                "a literal brace, or '{}' / '{0}' for a slot")
            inner = template[i + 1:close]
            if inner == "":
                autos += 1
                pieces.append(None)             # automatic slot
            elif inner.isdigit():
                idx = int(inner)                # {007} is 7 — digits only
                numbered.append(idx)
                pieces.append(idx)              # numbered slot
            else:
                raise JuRuGalti(line, col,
                                "format() slot '{{{}}}' is not a valid slot — a "
                                "slot is '{{}}' or '{{0}}', '{{1}}', '{{2}}', …"
                                .format(inner))
            i = close + 1
        elif ch == "}":
            if i + 1 < n and template[i + 1] == "}":
                pieces.append("}")
                i += 2
            else:
                raise JuRuGalti(line, col,
                                "format() found a lone '}' — write '}}' for "
                                "a literal brace")
        else:
            pieces.append(ch)
            i += 1

    if autos and numbered:
        raise JuRuGalti(line, col,
                        "format() cannot mix automatic {} slots and numbered "
                        "{0} slots — pick one style for the whole text")

    if autos:
        if len(values) < autos:
            need = autos - len(values)
            amount = "1 more value" if need == 1 else "{} more values".format(need)
            raise JuRuGalti(line, col,
                            "format() needs {} — the text has more {{}} "
                            "slots than values".format(amount))
        if len(values) > autos:
            raise JuRuGalti(line, col,
                            "format() got more values than slots — {} for {}"
                            .format(_count_word(len(values), "value"),
                                    _count_word(autos, "slot")))
        queue = list(values)
        return "".join(display(queue.pop(0)) if piece is None else piece
                       for piece in pieces)

    if numbered:
        for idx in numbered:                    # first bad slot, in text order
            if idx >= len(values):
                if values:
                    tail = "only {} given (0 to {})".format(
                        _count_word(len(values), "value"), len(values) - 1)
                else:
                    tail = "no values were given"
                raise JuRuGalti(line, col,
                                "format() slot {{{}}} does not exist — {}"
                                .format(idx, tail))
        span = max(numbered) + 1                # values fill positions 0…highest
        if len(values) > span:
            raise JuRuGalti(line, col,
                            "format() got more values than slots — {} for {}"
                            .format(_count_word(len(values), "value"),
                                    _count_word(span, "slot")))
        return "".join(display(values[piece]) if isinstance(piece, int)
                       else piece for piece in pieces)

    if values:                                  # no slots at all — extras are a mistake
        raise JuRuGalti(line, col,
                        "format() got more values than slots — {} for no slots"
                        .format(_count_word(len(values), "value")))
    return "".join(pieces)                      # all literal at this point


class Interpreter:
    MAX_SLEEP_ONE = 30        # seconds per sleep() call
    MAX_SLEEP_TOTAL = 120     # seconds a single run may sleep in total

    def __init__(self):
        self._modules = {}    # absolute path → ModuleValue (each file runs once)
        self._loading = []    # (path, base dir) stack — import loops die here
        self._call_stack = []  # (func name, call line) — recorded for errors
        self.sleep_total = 0.0
        self._builtin_call = self._make_builtin_call()

    def run(self, tree, env=None, base_dir=None):
        """Run the whole tree. Returns the final environment (for the REPL)."""
        if env is None:
            env = Env()
        self.base_dir = os.path.abspath(base_dir or os.getcwd())
        self._exec_block(tree.stmts, env)
        return env

    # ---------- statements ----------
    def _exec_block(self, stmts, env):
        for st in stmts:
            self._exec_stmt(st, env)

    def _exec_stmt(self, st, env):
        if isinstance(st, Assign):
            if st.name in BUILTINS:
                raise JuRuGalti(st.line, st.col,
                                "'{}' is reserved (builtin) — pick another name".format(st.name))
            if st.op is not None:         # x += e — the shorthand for x = x + e
                cur = self._lookup(st.name, st, env)
                env.vars[st.name] = self._op_apply(
                    st.line, st.col, st.op, cur, self.eval(st.value, env))
            else:
                env.vars[st.name] = self.eval(st.value, env)
            return

        if isinstance(st, SetIndex):
            seq = self.eval(st.seq, env)
            if isinstance(seq, dict):
                key = self._check_key(self.eval(st.idx, env), st.idx.line, st.idx.col)
                if st.op is not None:     # d["n"] += e — reads the old value first
                    if key not in seq:
                        self._missing_key(key, seq, st.idx)
                    seq[key] = self._op_apply(
                        st.line, st.col, st.op, seq[key], self.eval(st.value, env))
                else:
                    seq[key] = self.eval(st.value, env)
                return
            if not isinstance(seq, list):
                raise JuRuGalti(st.line, st.col,
                                "only lists and dicts support item assignment (this is {})".format(_typename(seq)))
            idx = self._check_index(seq, st.idx, env)
            if st.op is not None:         # xs[i] += e — reads the old item first
                seq[idx] = self._op_apply(
                    st.line, st.col, st.op, seq[idx], self.eval(st.value, env))
            else:
                seq[idx] = self.eval(st.value, env)
            return

        if isinstance(st, Say):
            parts = [display(self.eval(a, env)) for a in st.args]
            builtins.print(" ".join(parts))
            return

        if isinstance(st, If):
            if _truthy(self.eval(st.cond, env)):
                self._exec_block(st.then, env)
            elif st.orelse:
                self._exec_block(st.orelse, env)
            return

        if isinstance(st, TrySt):
            # only JuRu's own errors are catchable — a rescue never
            # swallows a bug inside JuRu itself or a signal (break,
            # continue, return) that is not an error at all
            try:
                self._exec_block(st.body, env)
            except JuRuGalti as err:
                renv = Env(env)            # the rescue gets its own scope
                if st.err_name:
                    renv.vars[st.err_name] = ErrV(err)
                self._exec_block(st.rescue, renv)
            return

        if isinstance(st, While):
            steps = 0
            while _truthy(self.eval(st.cond, env)):
                steps += 1
                if steps > MAX_LOOP_STEPS:
                    raise JuRuGalti(st.line, st.col,
                                    "the while loop ran over 10,000,000 times — it never stops?")
                try:
                    self._exec_block(st.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if isinstance(st, For):
            if st.iter is not None:
                self._exec_for_in(st, env)
                return
            start = self.eval(st.start, env)
            end = self.eval(st.end, env)
            for v in (start, end):
                if isinstance(v, bool) or not isinstance(v, int):
                    raise JuRuGalti(st.line, st.col,
                                    "for loop bounds must be whole numbers (int) — got: {}".format(display(v)))
            rng = range(start, end + 1) if start <= end else range(start, end - 1, -1)
            steps = 0
            for i in rng:
                steps += 1
                if steps > MAX_LOOP_STEPS:
                    raise JuRuGalti(st.line, st.col,
                                    "the for loop ran over 10,000,000 times — make the range smaller")
                env.vars[st.var] = i
                try:
                    self._exec_block(st.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if isinstance(st, Import):
            self._do_import(st, env)
            return

        if isinstance(st, FuncDef):
            if st.name in BUILTINS:
                raise JuRuGalti(st.line, st.col,
                                "'{}' is reserved (builtin) — pick another name".format(st.name))
            env.vars[st.name] = FuncValue(st.name, st.params, st.body, env)
            return

        if isinstance(st, Return):
            value = self.eval(st.value, env) if st.value is not None else None
            raise ReturnSignal(value)

        if isinstance(st, Break):
            raise BreakSignal()

        if isinstance(st, Continue):
            raise ContinueSignal()

        if isinstance(st, ExprSt):
            self.eval(st.expr, env)
            return

        raise JuRuGalti(st.line, st.col, "unknown statement: " + type(st).__name__)

    # ---------- for x in ... ----------
    def _exec_for_in(self, st, env):
        seq = self.eval(st.iter, env)
        if isinstance(seq, list):
            items = list(seq)          # iterate a copy — pushing during the loop is safe
        elif isinstance(seq, str):
            items = list(seq)          # one character at a time
        elif isinstance(seq, dict):
            items = list(seq.keys())   # dicts iterate over their keys
        elif isinstance(seq, SetV):
            items = list(seq.items)    # sets iterate their values, in order
        else:
            raise JuRuGalti(st.line, st.col,
                            "'for x in ...' needs a list, text, dict, or set — got: {}".format(display(seq)))
        steps = 0
        for item in items:
            steps += 1
            if steps > MAX_LOOP_STEPS:
                raise JuRuGalti(st.line, st.col,
                                "the for loop ran over 10,000,000 times — the value is too big")
            env.vars[st.var] = item
            try:
                self._exec_block(st.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    # ---------- dicts ----------
    @staticmethod
    def _check_key(key, line, col):
        """Dict keys are text or whole numbers — everything else is a mistake."""
        if isinstance(key, (str, int)) and not isinstance(key, bool):
            return key
        raise JuRuGalti(line, col,
                        "a dict key must be text or a whole number — got: {}".format(display(key)))

    @staticmethod
    def _missing_key(key, seq, node):
        shown = "'{}'".format(key) if isinstance(key, str) else display(key)
        head = "key {} was not found".format(shown)
        if isinstance(key, str):
            close = did_you_mean(key, list(seq.keys()))
            if close:
                head += " — did you mean '{}'?".format(close)
        if not seq:
            where = "this dict is empty"
        elif len(seq) > 6:
            where = "this dict has {} keys".format(len(seq))
        else:
            where = "this dict has: {}".format(
                ", ".join(display(k) for k in seq.keys()))
        raise JuRuGalti(node.line, node.col,
                        "{} — {}".format(head, where))

    # ---------- imports (Step 7) ----------
    def _do_import(self, st, env):
        if st.module in BUILTINS:                 # same refusal the checker makes
            raise JuRuGalti(st.line, st.col,
                            "the file '{}' would create the module '{}' — that name "
                            "is a reserved builtin; rename the file".format(st.path, st.module))
        base = self._loading[-1][1] if self._loading else self.base_dir
        path = os.path.normpath(os.path.join(base, st.path))
        if not os.path.isfile(path):
            raise JuRuGalti(st.line, st.col,
                            "cannot import '{}' — file not found (looked at: {})".format(st.path, path))
        if path in self._modules:                 # each file runs only once
            env.vars[st.module] = self._modules[path]
            return
        if any(p == path for p, _ in self._loading):
            chain = " -> ".join(os.path.basename(p) for p, _ in self._loading + [(path, base)])
            raise JuRuGalti(st.line, st.col,
                            "import loop: {} — a file cannot import itself, even through other files".format(chain))
        with open(path, encoding="utf-8") as f:
            src = f.read()
        try:
            tree = check_source(src)              # modules are checked too — no unchecked code runs
        except JuRuGalti as err:
            galti = JuRuGalti(err.line, err.col,
                              "in '{}': {}".format(st.path, err.message),
                              kind=err.kind)
            galti.stack = err.stack
            galti.source_file = path
            raise galti
        menv = Env()                              # a module sees nothing of the importer
        self._loading.append((path, os.path.dirname(path)))
        try:
            self._exec_block(tree.stmts, menv)
        except JuRuGalti as err:
            galti = JuRuGalti(err.line, err.col,
                              "in '{}': {}".format(st.path, err.message),
                              kind=err.kind)
            galti.stack = err.stack
            galti.source_file = path
            raise galti
        finally:
            self._loading.pop()
        mod = ModuleValue(st.module, menv, path)
        self._modules[path] = mod
        env.vars[st.module] = mod

    def _slice_part(self, node, env, label, default):
        """One slice bound: None → default; anything non-int is refused.

        Negative values are fine now — they count backwards, Python-style.
        """
        if node is None:
            return default
        v = self.eval(node, env)
        if isinstance(v, bool) or not isinstance(v, int):
            raise JuRuGalti(node.line, node.col,
                            "the slice {} must be a whole number (int) — got: {}".format(label, display(v)))
        return v

    def _member(self, seq, e):
        if isinstance(seq, dict):
            if e.name in seq:
                return seq[e.name]
            self._missing_key(e.name, seq, e)
        if isinstance(seq, ErrV):
            if e.name in ("message", "line", "col", "kind"):
                return getattr(seq, e.name)
            raise JuRuGalti(e.line, e.col,
                            "an error value has message, line, col and kind — not '{}'".format(e.name))
        if isinstance(seq, ModuleValue):
            if e.name in seq.env.vars:
                return seq.env.vars[e.name]
            close = did_you_mean(e.name, list(seq.env.vars))
            lead = " — did you mean '{}'?".format(close) if close else ""
            if not seq.env.vars:
                raise JuRuGalti(e.line, e.col,
                                "'{}' has no '{}' — the module is empty".format(seq.name, e.name))
            raise JuRuGalti(e.line, e.col,
                            "'{}' has no '{}'{} — the module has: {}".format(
                                seq.name, e.name, lead, ", ".join(seq.env.vars.keys())))
        raise JuRuGalti(e.line, e.col,
                        "'.' works on dicts and modules — got: {}".format(_typename(seq)))

    # ---------- expressions ----------
    def eval(self, e, env):
        if isinstance(e, Num):
            if "." in e.value:
                return float(e.value)
            return int(e.value)
        if isinstance(e, Text):
            return e.value
        if isinstance(e, Bool):
            return e.value
        if isinstance(e, Null):
            return None
        if isinstance(e, Name):
            return self._lookup(e.id, e, env)
        if isinstance(e, ListLit):
            return [self.eval(x, env) for x in e.items]
        if isinstance(e, UnaryOp):
            v = self.eval(e.operand, env)
            if e.op == "not":
                return not _truthy(v)
            if not _is_num(v):
                raise JuRuGalti(e.line, e.col,
                                "'{}' does not work on {} — a number is needed".format(e.op, _typename(v)))
            return -v if e.op == "-" else +v
        if isinstance(e, BinOp):
            return self._binop(e, env)
        if isinstance(e, Index):
            seq = self.eval(e.seq, env)
            if e.is_slice:
                if not isinstance(seq, (list, str)):
                    raise JuRuGalti(e.line, e.col,
                                    "slices work on lists and text — got: {}".format(display(seq)))
                start = self._slice_part(e.idx, env, "start", None)
                end = self._slice_part(e.idx_end, env, "end", None)
                step = self._slice_part(e.idx_step, env, "step", 1)
                if step == 0:
                    raise JuRuGalti(e.idx_step.line, e.idx_step.col,
                                    "the slice step cannot be zero")
                lo, hi, st = slice(start, end, step).indices(len(seq))
                if st < 0 and hi == -1:
                    hi = None        # indices() marks "down to the very start" as -1
                return seq[lo:hi:st]
            if isinstance(seq, dict):
                key = self._check_key(self.eval(e.idx, env), e.idx.line, e.idx.col)
                if key not in seq:
                    self._missing_key(key, seq, e.idx)
                return seq[key]
            if isinstance(seq, (list, str)):
                return seq[self._check_index(seq, e.idx, env)]
            raise JuRuGalti(e.line, e.col,
                            "only lists and text support indexing — got {}".format(_typename(seq)))
        if isinstance(e, Member):
            seq = self.eval(e.seq, env)
            return self._member(seq, e)
        if isinstance(e, DictLit):
            result = {}
            for k_node, v_node in zip(e.keys, e.values):
                key = self._check_key(self.eval(k_node, env), k_node.line, k_node.col)
                result[key] = self.eval(v_node, env)
            return result
        if isinstance(e, Call):
            return self._call(e, env)
        raise JuRuGalti(e.line, e.col, "unknown expression: " + type(e).__name__)

    def _lookup(self, name, node, env):
        e = env
        while e is not None:
            if name in e.vars:
                return e.vars[name]
            e = e.parent
        if name in ("dikhao", "bolo"):
            hint = " (the old 'bolo' is now 'say')"
        else:
            candidates = set()
            e = env
            while e is not None:
                candidates.update(e.vars)
                e = e.parent
            close = did_you_mean(name, candidates)
            hint = " — did you mean '{}'?".format(close) if close else ""
        raise JuRuGalti(node.line, node.col,
                        "'{}' was not found{}".format(name, hint))

    def _check_index(self, seq, idx_node, env):
        idx = self.eval(idx_node, env)
        if isinstance(idx, bool) or not isinstance(idx, int):
            raise JuRuGalti(idx_node.line, idx_node.col,
                            "the index must be a whole number (int) — got: {}".format(display(idx)))
        n = len(seq)
        # negative indexes count backwards: -1 is the last item, -len is the first
        if not -n <= idx < n:
            low = -n if idx < 0 else 0
            raise JuRuGalti(idx_node.line, idx_node.col,
                            "index {} is out of range — this {} has {} items ({} to {})".format(
                                idx, _typename(seq), n, low, n - 1))
        return idx + n if idx < 0 else idx

    def _binop(self, e, env):
        op = e.op
        if op == "and":
            if not _truthy(self.eval(e.left, env)):
                return False
            return _truthy(self.eval(e.right, env))
        if op == "or":
            if _truthy(self.eval(e.left, env)):
                return True
            return _truthy(self.eval(e.right, env))

        left = self.eval(e.left, env)
        right = self.eval(e.right, env)
        return self._op_apply(e.line, e.col, op, left, right)

    def _op_apply(self, line, col, op, left, right):
        """Apply one binary operator to two VALUES (already evaluated).

        Shared by `a + b` and by the augmented shorthands: x += e,
        xs[i] -= e — one rule table, never two.
        """
        if op in ("in", "not in"):
            found = self._membership(left, right, line, col)
            return found if op == "in" else not found

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                if isinstance(left, (list, FuncValue)) or isinstance(right, (list, FuncValue)):
                    raise JuRuGalti(line, col,
                                    "a list or func cannot be joined with text")
                return display(left) + display(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if _is_num(left) and _is_num(right):
                return left + right
            raise JuRuGalti(line, col,
                            "cannot use '+' on {} and {}".format(_typename(left), _typename(right)))

        if op in ("-", "*", "/", "%"):
            if op == "*" and isinstance(left, str):
                if isinstance(right, int) and not isinstance(right, bool) and right >= 0:
                    if len(left) * right > MAX_LOOP_STEPS:
                        raise JuRuGalti(line, col,
                                        "text * {} would be too big — text cannot grow "
                                        "over 10,000,000 characters".format(display(right)))
                    return left * right
                raise JuRuGalti(line, col,
                                "text * number needs a whole number (0 or more) — got: {}".format(
                                    display(right)))
            if not (_is_num(left) and _is_num(right)):
                raise JuRuGalti(line, col,
                                "'{}' only works on numbers — got {} and {}".format(
                                    op, _typename(left), _typename(right)))
            if op == "/" and right == 0:
                raise JuRuGalti(line, col, "cannot divide by zero (x / 0)")
            if op == "%" and right == 0:
                raise JuRuGalti(line, col, "cannot use '%' with zero (x % 0)")
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                return left / right
            return left % right

        if op in ("==", "!="):
            same = self._equals(left, right)
            return same if op == "==" else not same

        if op in ("<", "<=", ">", ">="):
            if not ((_is_num(left) and _is_num(right)) or
                    (isinstance(left, str) and isinstance(right, str))):
                raise JuRuGalti(line, col,
                                "'{}' cannot compare {} and {} — different worlds".format(
                                    op, _typename(left), _typename(right)))
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right

        raise JuRuGalti(line, col, "unknown operator: " + op)

    def _membership(self, item, container, line, col):
        """x in list / x in text / key in dict / x in set (and 'not in')."""
        if isinstance(container, list):
            return any(self._equals(item, x) for x in container)
        if isinstance(container, str):
            if not isinstance(item, str):
                raise JuRuGalti(line, col,
                                "'in' on text needs text on the left — got: {}".format(display(item)))
            return item in container
        if isinstance(container, dict):
            key = self._check_key(item, line, col)
            return key in container
        if isinstance(container, SetV):
            return any(self._equals(item, x) for x in container.items)
        raise JuRuGalti(line, col,
                        "'in' needs a list, text, dict, or set on the right — got: {}".format(display(container)))

    @staticmethod
    def _equals(a, b):
        # true != 1 (different categories), but 1 == 1.0 (same number family)
        return _same_value(a, b)

    def _call(self, e, env):
        if e.callee is not None:                    # utils.double(...) / mod tools
            func = self.eval(e.callee, env)
        elif e.name in BUILTINS:
            return self._builtin(e, env)
        else:
            func = self._lookup(e.name, e, env)
        if not isinstance(func, FuncValue):
            raise JuRuGalti(e.line, e.col,
                            "'{}' cannot be called — it is not a func (it is {})".format(
                                e.name, _typename(func)))
        if len(e.args) != len(func.params):
            word = "argument" if len(func.params) == 1 else "arguments"
            raise JuRuGalti(e.line, e.col,
                            "func '{}' expects {} {}, you gave {}".format(
                                e.name, len(func.params), word, len(e.args)))
        cenv = Env(func.env)
        for p, a in zip(func.params, e.args):
            cenv.vars[p] = self.eval(a, env)
        self._call_stack.append((func.name, e.line))
        try:
            self._exec_block(func.body, cenv)
        except ReturnSignal as r:
            return r.value
        except JuRuGalti as err:
            # the innermost call boundary records the stack ONCE — later
            # frames (and try/rescue) keep the original, never overwrite
            if getattr(err, "stack", None) is None:
                err.stack = tuple(self._call_stack)
            raise
        except RecursionError:
            raise JuRuGalti(e.line, e.col,
                            "recursion went too deep — it never stops")
        finally:
            self._call_stack.pop()
        return None

    # ---------- builtins (the registry lives in stdlib.py) ----------
    # Every builtin is a small method here; the shared rules (name,
    # argument count, the exact refusal message) live in ONE table.
    def _builtin(self, e, env):
        bad = check_arity(e.name, len(e.args))
        if bad is not None:
            raise JuRuGalti(e.line, e.col, bad)
        return self._builtin_call[e.name](e, env)

    def _bi_ask(self, e, env):
        prompt = display(self.eval(e.args[0], env)) if e.args else ""
        try:
            return builtins.input(prompt)
        except EOFError:
            raise JuRuGalti(
                e.line, e.col,
                "ask() could not read any more input — the program was "
                "waiting for an answer and the input ended")

    def _bi_len(self, e, env):
        v = self.eval(e.args[0], env)
        if isinstance(v, (str, list, dict, SetV)):
            return len(v)
        raise JuRuGalti(e.line, e.col,
                        "'{}' has no length — only text, lists, dicts and sets do".format(_typename(v)))

    def _bi_int(self, e, env):
        v = self.eval(e.args[0], env)
        if isinstance(v, bool) or v is None or isinstance(
                v, (list, dict, FuncValue, ModuleValue)):
            raise JuRuGalti(e.line, e.col,
                            "int({}) — this cannot be converted to int".format(display(v)))
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        try:
            return int(v.strip())
        except ValueError:
            raise JuRuGalti(e.line, e.col,
                            "int('{}') — '{}' is not a whole number".format(v, v))

    def _bi_float(self, e, env):
        v = self.eval(e.args[0], env)
        if isinstance(v, bool) or v is None or isinstance(
                v, (list, dict, FuncValue, ModuleValue)):
            raise JuRuGalti(e.line, e.col,
                            "float({}) — this cannot be converted to float".format(display(v)))
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v.strip())
        except ValueError:
            raise JuRuGalti(e.line, e.col,
                            "float('{}') — '{}' is not a number".format(v, v))

    def _bi_upper(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "upper() needs text — got: {}".format(display(v)))
        return v.upper()

    def _bi_lower(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "lower() needs text — got: {}".format(display(v)))
        return v.lower()

    def _bi_str(self, e, env):
        return display(self.eval(e.args[0], env))

    def _bi_push(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "push() needs a list — got: {}".format(display(lst)))
        lst.append(self.eval(e.args[1], env))
        return lst

    def _bi_pop(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "pop() needs a list — got: {}".format(display(lst)))
        if not lst:
            raise JuRuGalti(e.line, e.col,
                            "pop() — this list is empty, there is nothing to take")
        return lst.pop()

    def _bi_sum(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, list):
            raise JuRuGalti(e.line, e.col,
                            "sum() needs a list — got: {}".format(display(v)))
        total = 0
        for item in v:
            if not _is_num(item):
                raise JuRuGalti(e.line, e.col,
                                "sum() needs only numbers — found: {}".format(display(item)))
            total = total + item
        return total

    def _bi_min(self, e, env):
        values = [self.eval(a, env) for a in e.args]
        if len(values) == 1 and isinstance(values[0], list):
            values = list(values[0])          # min(list) — scan the list
            if not values:
                raise JuRuGalti(e.line, e.col,
                                "min() — this list is empty, there is nothing to compare")
            for item in values:
                if not _is_num(item):
                    raise JuRuGalti(e.line, e.col,
                                    "min() needs only numbers — found: {}".format(display(item)))
        elif len(values) == 2:
            # the classic pair — the message stayed exactly as it always was
            a, b = values
            if not (_is_num(a) and _is_num(b)):
                raise JuRuGalti(e.line, e.col,
                                "min() needs numbers — got {} and {}".format(
                                    _typename(a), _typename(b)))
        else:
            for v in values:
                if not _is_num(v):
                    raise JuRuGalti(e.line, e.col,
                                    "min() needs numbers — got: {}".format(_typename(v)))
        return min(values)

    def _bi_max(self, e, env):
        values = [self.eval(a, env) for a in e.args]
        if len(values) == 1 and isinstance(values[0], list):
            values = list(values[0])          # max(list) — scan the list
            if not values:
                raise JuRuGalti(e.line, e.col,
                                "max() — this list is empty, there is nothing to compare")
            for item in values:
                if not _is_num(item):
                    raise JuRuGalti(e.line, e.col,
                                    "max() needs only numbers — found: {}".format(display(item)))
        elif len(values) == 2:
            # the classic pair — the message stayed exactly as it always was
            a, b = values
            if not (_is_num(a) and _is_num(b)):
                raise JuRuGalti(e.line, e.col,
                                "max() needs numbers — got {} and {}".format(
                                    _typename(a), _typename(b)))
        else:
            for v in values:
                if not _is_num(v):
                    raise JuRuGalti(e.line, e.col,
                                    "max() needs numbers — got: {}".format(_typename(v)))
        return max(values)

    def _bi_split(self, e, env):
        v = self.eval(e.args[0], env)
        sep = self.eval(e.args[1], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "split() needs text — got: {}".format(display(v)))
        if not isinstance(sep, str):
            raise JuRuGalti(e.line, e.col,
                            "the split separator must be text — got: {}".format(display(sep)))
        if sep == "":
            raise JuRuGalti(e.line, e.col,
                            "the split separator cannot be empty")
        return v.split(sep)

    def _bi_join(self, e, env):
        lst = self.eval(e.args[0], env)
        sep = self.eval(e.args[1], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "join() needs a list — got: {}".format(display(lst)))
        if not isinstance(sep, str):
            raise JuRuGalti(e.line, e.col,
                            "the join separator must be text — got: {}".format(display(sep)))
        return sep.join(display(x) for x in lst)

    def _bi_trim(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "trim() needs text — got: {}".format(display(v)))
        return v.strip()

    def _bi_replace(self, e, env):
        v = self.eval(e.args[0], env)
        old = self.eval(e.args[1], env)
        new = self.eval(e.args[2], env)
        for part in (v, old, new):
            if not isinstance(part, str):
                raise JuRuGalti(e.line, e.col,
                                "replace() needs text — got: {}".format(display(part)))
        if old == "":
            raise JuRuGalti(e.line, e.col,
                            "the old text cannot be empty in replace()")
        return v.replace(old, new)

    def _bi_abs(self, e, env):
        v = self.eval(e.args[0], env)
        if not _is_num(v):
            raise JuRuGalti(e.line, e.col,
                            "abs() needs a number — got: {}".format(display(v)))
        return abs(v)

    def _bi_round(self, e, env):
        v = self.eval(e.args[0], env)
        if not _is_num(v):
            raise JuRuGalti(e.line, e.col,
                            "round() needs a number — got: {}".format(display(v)))
        if isinstance(v, int):
            return v
        # half away from zero: 2.5 → 3, -2.5 → -3 (no surprises)
        return int(v + 0.5) if v >= 0 else int(v - 0.5)

    def _bi_random(self, e, env):
        low = self.eval(e.args[0], env)
        high = self.eval(e.args[1], env)
        for v in (low, high):
            if isinstance(v, bool) or not isinstance(v, int):
                raise JuRuGalti(e.line, e.col,
                                "random() needs whole numbers — got: {}".format(display(v)))
        if low > high:
            raise JuRuGalti(e.line, e.col,
                            "in random(low, high), low cannot be bigger than high ({} > {})".format(low, high))
        return _random.randint(low, high)

    def _bi_sqrt(self, e, env):
        v = self.eval(e.args[0], env)
        if not _is_num(v):
            raise JuRuGalti(e.line, e.col,
                            "sqrt() needs a number — got: {}".format(display(v)))
        if v < 0:
            raise JuRuGalti(e.line, e.col,
                            "sqrt({}) — a negative number has no square root".format(display(v)))
        return v ** 0.5

    def _bi_sorted(self, e, env):
        v = self.eval(e.args[0], env)
        items = v.items if isinstance(v, SetV) else v
        if not isinstance(items, list):
            raise JuRuGalti(e.line, e.col,
                            "sorted() needs a list — got: {}".format(display(v)))
        if not all(_is_num(x) for x in items) and not all(isinstance(x, str) for x in items):
            raise JuRuGalti(e.line, e.col,
                            "sorted() needs a list of only numbers or only text — got: {}".format(display(v)))
        return sorted(items)      # a NEW list — the original stays as it is

    def _bi_reverse(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, list):
            raise JuRuGalti(e.line, e.col,
                            "reverse() needs a list — got: {}".format(display(v)))
        return list(reversed(v))  # a NEW list — the original stays as it is

    def _bi_find(self, e, env):
        lst = self.eval(e.args[0], env)
        target = self.eval(e.args[1], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "find() needs a list first — got: {}".format(display(lst)))
        for i, x in enumerate(lst):
            if self._equals(x, target):
                return i
        return -1                 # not found — a plain -1, easy to check

    def _bi_keys(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, dict):
            raise JuRuGalti(e.line, e.col,
                            "keys() needs a dict — got: {}".format(display(v)))
        return list(v.keys())

    def _bi_values(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, dict):
            raise JuRuGalti(e.line, e.col,
                            "values() needs a dict — got: {}".format(display(v)))
        return list(v.values())

    def _bi_count(self, e, env):
        lst = self.eval(e.args[0], env)
        target = self.eval(e.args[1], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "count() needs a list first — got: {}".format(display(lst)))
        return sum(1 for x in lst if self._equals(x, target))

    def _bi_pow(self, e, env):
        a = self.eval(e.args[0], env)
        b = self.eval(e.args[1], env)
        if not _is_num(a) or not _is_num(b):
            raise JuRuGalti(e.line, e.col,
                            "pow() needs numbers — got: {} and {}".format(
                                _typename(a), _typename(b)))
        if a == 0 and b < 0:
            raise JuRuGalti(e.line, e.col,
                            "in pow(a, b), 0 cannot be raised to a negative power")
        if a < 0 and b != int(b):
            raise JuRuGalti(e.line, e.col,
                            "in pow(a, b), a negative base needs a whole-number "
                            "exponent (got: {})".format(display(b)))
        if isinstance(a, int) and isinstance(b, int) \
                and abs(b) > 10000 and abs(a) > 1:
            raise JuRuGalti(e.line, e.col,
                            "pow({}, {}) — the result is too big to show".format(
                                display(a), display(b)))
        try:
            return a ** b
        except OverflowError:
            raise JuRuGalti(e.line, e.col, "pow(...) — the result is too big to show")

    def _bi_type(self, e, env):
        return _typename(self.eval(e.args[0], env))

    def _bi_help(self, e, env):
        if not e.args:
            print(overview())
            return None
        topic = self.eval(e.args[0], env)
        if not isinstance(topic, str):
            raise JuRuGalti(e.line, e.col,
                            "help() needs a name in quotes — got: {}".format(
                                display(topic)))
        text = card_for(topic)
        if text is None:
            print(unknown(topic))
            return None
        print(text)
        return None

    def _bi_sleep(self, e, env):
        v = self.eval(e.args[0], env)
        if not _is_num(v):
            raise JuRuGalti(e.line, e.col,
                            "sleep() needs a number of seconds — got: {}".format(
                                _typename(v)))
        if v < 0:
            raise JuRuGalti(e.line, e.col,
                            "sleep() cannot go back in time — seconds cannot "
                            "be negative (got: {})".format(display(v)))
        if v > self.MAX_SLEEP_ONE:
            raise JuRuGalti(e.line, e.col,
                            "sleep() takes at most {} seconds at a time "
                            "(got: {})".format(self.MAX_SLEEP_ONE, display(v)))
        if self.sleep_total + v > self.MAX_SLEEP_TOTAL:
            raise JuRuGalti(e.line, e.col,
                            "sleep() — this program has slept more than {} "
                            "seconds in total; something may be stuck".format(
                                self.MAX_SLEEP_TOTAL))
        time.sleep(v)
        self.sleep_total += v
        return None

    # ---------- Step 23: errors you can catch ----------
    def _bi_fail(self, e, env):
        """fail(message) — raise your own JuRu error (kind 'fail').

        The message is used VERBATIM; the error is born at the fail()
        call's line/col and is caught by the nearest rescue like any
        other JuRu error.
        """
        msg = self.eval(e.args[0], env)
        if not isinstance(msg, str):
            raise JuRuGalti(e.line, e.col,
                            "fail() needs a message in quotes — got: {}".format(
                                _typename(msg)))
        raise JuRuGalti(e.line, e.col, msg, kind="fail")

    # ---------- Step 22: collections & ergonomics ----------
    def _bi_insert(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "insert() needs a list — got: {}".format(display(lst)))
        i = self.eval(e.args[1], env)
        if isinstance(i, bool) or not isinstance(i, int):
            raise JuRuGalti(e.line, e.col,
                            "insert() needs a whole number (int) — got: {}".format(display(i)))
        lst.insert(i, self.eval(e.args[2], env))
        # Python-like: a negative i counts backwards, a big i clamps to the end
        return lst

    def _bi_remove_at(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "remove_at() needs a list — got: {}".format(display(lst)))
        idx = self._check_index(lst, e.args[1], env)   # bounds-checked, -1 = last
        return lst.pop(idx)

    def _bi_clear(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "clear() needs a list — got: {}".format(display(lst)))
        del lst[:]
        return lst

    def _bi_extend(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "extend() needs a list — got: {}".format(display(lst)))
        more = self.eval(e.args[1], env)
        if not isinstance(more, list):
            raise JuRuGalti(e.line, e.col,
                            "the extend items must be a list — got: {}".format(display(more)))
        lst.extend(more)
        return lst

    def _bi_unique(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "unique() needs a list — got: {}".format(display(lst)))
        seen = SetV(lst)          # first occurrence wins, same equality as ==
        return list(seen.items)   # a NEW list — the original stays as it is

    def _bi_delete(self, e, env):
        d = self.eval(e.args[0], env)
        if not isinstance(d, dict):
            raise JuRuGalti(e.line, e.col,
                            "delete() needs a dict — got: {}".format(display(d)))
        key = self._check_key(self.eval(e.args[1], env), e.args[1].line, e.args[1].col)
        if key not in d:
            self._missing_key(key, d, e.args[1])
        del d[key]
        return d

    def _bi_items(self, e, env):
        d = self.eval(e.args[0], env)
        if not isinstance(d, dict):
            raise JuRuGalti(e.line, e.col,
                            "items() needs a dict — got: {}".format(display(d)))
        return [[k, v] for k, v in d.items()]

    def _bi_merge(self, e, env):
        a = self.eval(e.args[0], env)
        b = self.eval(e.args[1], env)
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise JuRuGalti(e.line, e.col,
                            "merge() needs dicts — got: {} and {}".format(
                                _typename(a), _typename(b)))
        out = dict(a)
        out.update(b)             # a NEW dict — later keys win
        return out

    def _bi_index_of(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "index_of() needs text — got: {}".format(display(v)))
        piece = self.eval(e.args[1], env)
        if not isinstance(piece, str):
            raise JuRuGalti(e.line, e.col,
                            "the index_of piece must be text — got: {}".format(display(piece)))
        if piece == "":
            raise JuRuGalti(e.line, e.col,
                            "the index_of piece cannot be empty")
        return v.find(piece)      # first index, or -1 — mirrors find() on lists

    def _bi_starts_with(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "starts_with() needs text — got: {}".format(display(v)))
        prefix = self.eval(e.args[1], env)
        if not isinstance(prefix, str):
            raise JuRuGalti(e.line, e.col,
                            "the starts_with prefix must be text — got: {}".format(display(prefix)))
        if prefix == "":
            raise JuRuGalti(e.line, e.col,
                            "the starts_with prefix cannot be empty")
        return v.startswith(prefix)

    def _bi_ends_with(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "ends_with() needs text — got: {}".format(display(v)))
        suffix = self.eval(e.args[1], env)
        if not isinstance(suffix, str):
            raise JuRuGalti(e.line, e.col,
                            "the ends_with suffix must be text — got: {}".format(display(suffix)))
        if suffix == "":
            raise JuRuGalti(e.line, e.col,
                            "the ends_with suffix cannot be empty")
        return v.endswith(suffix)

    def _bi_ord(self, e, env):
        v = self.eval(e.args[0], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "ord() needs text — got: {}".format(display(v)))
        if len(v) != 1:
            raise JuRuGalti(e.line, e.col,
                            "ord() needs exactly one character — got {}".format(len(v)))
        return ord(v)

    def _bi_chr(self, e, env):
        v = self.eval(e.args[0], env)
        if isinstance(v, bool) or not isinstance(v, int):
            raise JuRuGalti(e.line, e.col,
                            "chr() needs a whole number (int) — got: {}".format(display(v)))
        if not 0 <= v <= 0x10FFFF:
            raise JuRuGalti(e.line, e.col,
                            "chr({}) — the code must be between 0 and 1114111".format(display(v)))
        if 0xD800 <= v <= 0xDFFF:
            raise JuRuGalti(e.line, e.col,
                            "chr({}) — codes 55296 to 57343 are reserved; "
                            "this character cannot be shown".format(display(v)))
        return chr(v)

    # ---------- Step 24: text & formatting ----------
    MAX_PAD_WIDTH = 10000    # characters at a time — no runaway allocation

    def _pad_width(self, e, env, name):
        """The validated width for pad_left/pad_right/center."""
        n = self.eval(e.args[1], env)
        if isinstance(n, bool) or not isinstance(n, int):
            raise JuRuGalti(e.line, e.col,
                            "{}() needs a whole-number width — got: {}".format(
                                name, display(n)))
        if n < 0:
            raise JuRuGalti(e.line, e.col,
                            "{}() width cannot be negative — got: {}".format(
                                name, display(n)))
        if n > self.MAX_PAD_WIDTH:
            raise JuRuGalti(e.line, e.col,
                            "{}() width is too big — at most {} characters "
                            "at a time".format(name, self.MAX_PAD_WIDTH))
        return n

    def _pad_text(self, e, env, name):
        text = self.eval(e.args[0], env)
        if not isinstance(text, str):
            raise JuRuGalti(e.line, e.col,
                            "{}() needs text — got: {}".format(name, display(text)))
        return text, self._pad_width(e, env, name)

    def _bi_pad_left(self, e, env):
        text, width = self._pad_text(e, env, "pad_left")
        gap = width - _display_width(text)
        if gap <= 0:
            return text                       # never truncates
        return " " * gap + text

    def _bi_pad_right(self, e, env):
        text, width = self._pad_text(e, env, "pad_right")
        gap = width - _display_width(text)
        if gap <= 0:
            return text                       # never truncates
        return text + " " * gap

    def _bi_center(self, e, env):
        text, width = self._pad_text(e, env, "center")
        gap = width - _display_width(text)
        if gap <= 0:
            return text                       # never truncates
        left = gap // 2
        right = gap - left                    # an odd extra space goes right (pinned)
        return " " * left + text + " " * right

    def _bi_split_lines(self, e, env):
        text = self.eval(e.args[0], env)
        if not isinstance(text, str):
            raise JuRuGalti(e.line, e.col,
                            "split_lines() needs text — got: {}".format(
                                display(text)))
        return _lines_from_text(text)

    def _bi_join_lines(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "join_lines() needs a list — got: {}".format(
                                display(lst)))
        for i, line in enumerate(lst):
            if not isinstance(line, str):
                raise JuRuGalti(e.line, e.col,
                                "join_lines() needs every line to be text — "
                                "got: {} at position {}".format(
                                    display(line), i + 1))
        return "\n".join(lst)

    # ---------- Step 25: files & JSON ----------
    MAX_FILE_BYTES = 10 * 1024 * 1024      # 10 MB per read/write/JSON text
    MAX_JSON_DEPTH = 64                    # nested lists/dicts, one level each
    MAX_DIR_ENTRIES = 10000                # list_dir()'s sanity cap

    @staticmethod
    def _bytes_text(n):
        return "{} bytes".format(n)

    def _file_path(self, e, env, name, arg=0):
        """The validated (shown, absolute) path for a file builtin.

        Relative paths resolve against the running program's directory,
        exactly like imports; absolute paths are used as they are. No ~
        expansion, no globs.
        """
        v = self.eval(e.args[arg], env)
        if not isinstance(v, str):
            raise JuRuGalti(e.line, e.col,
                            "{}() needs a file path in text — got: {}".format(
                                name, display(v)), kind="type")
        if v == "":
            raise JuRuGalti(e.line, e.col,
                            "{}() needs a file path — it cannot be empty".format(
                                name), kind="value")
        if "\x00" in v:
            raise JuRuGalti(
                e.line, e.col,
                "{}() needs a file path without NUL characters — a file "
                "name cannot contain one".format(name), kind="value")
        path = v if os.path.isabs(v) else os.path.join(self.base_dir, v)
        return v, os.path.normpath(path)

    def _read_text_file(self, e, name, shown, path):
        """Read one UTF-8 file with the size cap and friendly failures."""
        try:
            if os.path.isdir(path):
                raise JuRuGalti(
                    e.line, e.col,
                    "{}() could not read '{}' — it is a folder, not a file".format(
                        name, shown), kind="file")
            if not os.path.isfile(path):
                raise JuRuGalti(
                    e.line, e.col,
                    "{}() could not read '{}' — file not found (looked at: {})".format(
                        name, shown, path), kind="file")
            size = os.path.getsize(path)
            if size > self.MAX_FILE_BYTES:
                raise JuRuGalti(
                    e.line, e.col,
                    "{}() could not read '{}' — the file is too big ({}; the "
                    "limit is 10 MB)".format(name, shown, self._bytes_text(size)),
                    kind="file")
            with open(path, encoding="utf-8", newline="") as f:
                return f.read()
        except UnicodeDecodeError:
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not read '{}' — the file is not valid UTF-8 "
                "text".format(name, shown), kind="file")
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not read '{}' — {}".format(
                    name, shown, err.strerror or "the system refused"),
                kind="file")

    def _write_text_file(self, e, name, shown, path, text, append=False):
        """Write/append one UTF-8 file with the size cap and friendly failures."""
        data_len = len(text.encode("utf-8"))
        try:
            existing = os.path.getsize(path) if append and os.path.isfile(path) else 0
        except OSError:
            existing = 0
        if existing + data_len > self.MAX_FILE_BYTES:
            verb = "append to" if append else "write"
            what = ("the file would become too big" if append
                    else "the text is too big")
            total = existing + data_len
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not {} '{}' — {} ({}; the limit is 10 MB)".format(
                    name, verb, shown, what, self._bytes_text(total)),
                kind="file")
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not write '{}' — the folder does not exist".format(
                    name, shown), kind="file")
        if os.path.isdir(path):
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not write '{}' — it is a folder, not a file".format(
                    name, shown), kind="file")
        try:
            with open(path, "a" if append else "w", encoding="utf-8",
                      newline="") as f:
                f.write(text)
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "{}() could not write '{}' — {}".format(
                    name, shown, err.strerror or "the system refused"),
                kind="file")

    def _bi_read_file(self, e, env):
        shown, path = self._file_path(e, env, "read_file")
        return self._read_text_file(e, "read_file", shown, path)

    def _bi_write_file(self, e, env):
        shown, path = self._file_path(e, env, "write_file")
        text = self.eval(e.args[1], env)
        if not isinstance(text, str):
            raise JuRuGalti(e.line, e.col,
                            "write_file() needs text to write — got: {}".format(
                                display(text)), kind="type")
        self._write_text_file(e, "write_file", shown, path, text)
        return None

    def _bi_append_file(self, e, env):
        shown, path = self._file_path(e, env, "append_file")
        text = self.eval(e.args[1], env)
        if not isinstance(text, str):
            raise JuRuGalti(e.line, e.col,
                            "append_file() needs text to append — got: {}".format(
                                display(text)), kind="type")
        self._write_text_file(e, "append_file", shown, path, text, append=True)
        return None

    def _bi_read_lines(self, e, env):
        shown, path = self._file_path(e, env, "read_lines")
        return _lines_from_text(self._read_text_file(e, "read_lines", shown, path))

    def _bi_write_lines(self, e, env):
        shown, path = self._file_path(e, env, "write_lines")
        lines = self.eval(e.args[1], env)
        if not isinstance(lines, list):
            raise JuRuGalti(e.line, e.col,
                            "write_lines() needs a list of lines — got: {}".format(
                                display(lines)), kind="type")
        for i, line in enumerate(lines):
            if not isinstance(line, str):
                raise JuRuGalti(
                    e.line, e.col,
                    "write_lines() needs every line to be text — got: {} at "
                    "position {}".format(display(line), i + 1), kind="type")
            if "\n" in line or "\r" in line:
                raise JuRuGalti(
                    e.line, e.col,
                    "write_lines() needs each line to be ONE line — line {} "
                    "contains a newline".format(i + 1), kind="value")
        text = "\n".join(lines)
        if lines:
            text += "\n"          # so read_lines(write_lines(xs)) == xs
        self._write_text_file(e, "write_lines", shown, path, text)
        return None

    def _bi_file_exists(self, e, env):
        shown, path = self._file_path(e, env, "file_exists")
        return os.path.exists(path)

    def _bi_file_size(self, e, env):
        shown, path = self._file_path(e, env, "file_size")
        if os.path.isdir(path):
            raise JuRuGalti(
                e.line, e.col,
                "file_size() needs a file — '{}' is a folder".format(shown),
                kind="file")
        if not os.path.exists(path):
            raise JuRuGalti(
                e.line, e.col,
                "file_size() could not measure '{}' — file not found (looked "
                "at: {})".format(shown, path), kind="file")
        try:
            return os.path.getsize(path)
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "file_size() could not measure '{}' — {}".format(
                    shown, err.strerror or "the system refused"), kind="file")

    def _bi_delete_file(self, e, env):
        shown, path = self._file_path(e, env, "delete_file")
        if os.path.isdir(path):
            raise JuRuGalti(
                e.line, e.col,
                "delete_file() refuses a folder — '{}' is a folder; use "
                "delete_dir()".format(shown), kind="file")
        if not os.path.exists(path):
            raise JuRuGalti(
                e.line, e.col,
                "delete_file() could not delete '{}' — file not found (looked "
                "at: {})".format(shown, path), kind="file")
        try:
            os.remove(path)
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "delete_file() could not delete '{}' — {}".format(
                    shown, err.strerror or "the system refused"), kind="file")
        return None

    def _bi_list_dir(self, e, env):
        shown, path = self._file_path(e, env, "list_dir")
        if not os.path.exists(path):
            raise JuRuGalti(
                e.line, e.col,
                "list_dir() could not list '{}' — folder not found (looked at: "
                "{})".format(shown, path), kind="file")
        if not os.path.isdir(path):
            raise JuRuGalti(
                e.line, e.col,
                "list_dir() needs a folder — '{}' is a file".format(shown),
                kind="file")
        try:
            names = sorted(os.listdir(path))
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "list_dir() could not list '{}' — {}".format(
                    shown, err.strerror or "the system refused"), kind="file")
        if len(names) > self.MAX_DIR_ENTRIES:
            raise JuRuGalti(
                e.line, e.col,
                "list_dir() found too many names — at most {} at a time".format(
                    self.MAX_DIR_ENTRIES), kind="value")
        return names

    def _bi_make_dir(self, e, env):
        shown, path = self._file_path(e, env, "make_dir")
        if os.path.isdir(path):
            return None                       # already there — friendly no-op
        if os.path.exists(path):
            raise JuRuGalti(
                e.line, e.col,
                "make_dir() could not create '{}' — a file with that name "
                "already exists".format(shown), kind="file")
        try:
            os.makedirs(path)                 # parents too, one function
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "make_dir() could not create '{}' — {}".format(
                    shown, err.strerror or "the system refused"), kind="file")
        return None

    def _bi_delete_dir(self, e, env):
        shown, path = self._file_path(e, env, "delete_dir")
        if not os.path.exists(path):
            raise JuRuGalti(
                e.line, e.col,
                "delete_dir() could not delete '{}' — folder not found (looked "
                "at: {})".format(shown, path), kind="file")
        if not os.path.isdir(path):
            raise JuRuGalti(
                e.line, e.col,
                "delete_dir() needs a folder — '{}' is a file".format(shown),
                kind="file")
        try:
            if os.listdir(path):
                raise JuRuGalti(
                    e.line, e.col,
                    "delete_dir() only removes an EMPTY folder — '{}' still has "
                    "things in it".format(shown), kind="file")
            os.rmdir(path)
        except JuRuGalti:
            raise
        except OSError as err:
            raise JuRuGalti(
                e.line, e.col,
                "delete_dir() could not delete '{}' — {}".format(
                    shown, err.strerror or "the system refused"), kind="file")
        return None

    def _json_check(self, v, e, seen, level):
        """Validate a JuRu value for to_json (types, keys, depth, cycles)."""
        if v is None or isinstance(v, (bool, int, str)):
            return
        if isinstance(v, float):
            if not math.isfinite(v):
                raise JuRuGalti(
                    e.line, e.col,
                    "to_json() cannot write a number that is not finite — "
                    "JSON has no NaN or Infinity", kind="value")
            return
        if isinstance(v, list):
            if level > self.MAX_JSON_DEPTH:
                raise JuRuGalti(
                    e.line, e.col,
                    "to_json() found a value nested too deeply — the limit is "
                    "{} levels".format(self.MAX_JSON_DEPTH), kind="value")
            if id(v) in seen:
                raise JuRuGalti(
                    e.line, e.col,
                    "to_json() cannot write a value that contains itself",
                    kind="value")
            seen.add(id(v))
            for item in v:
                self._json_check(item, e, seen, level + 1)
            seen.discard(id(v))
            return
        if isinstance(v, dict):
            if level > self.MAX_JSON_DEPTH:
                raise JuRuGalti(
                    e.line, e.col,
                    "to_json() found a value nested too deeply — the limit is "
                    "{} levels".format(self.MAX_JSON_DEPTH), kind="value")
            if id(v) in seen:
                raise JuRuGalti(
                    e.line, e.col,
                    "to_json() cannot write a value that contains itself",
                    kind="value")
            seen.add(id(v))
            for key, item in v.items():
                if not isinstance(key, str):
                    raise JuRuGalti(
                        e.line, e.col,
                        "to_json() needs text keys in every dict — found {} "
                        "(JSON keys are always text)".format(display(key)),
                        kind="type")
                self._json_check(item, e, seen, level + 1)
            seen.discard(id(v))
            return
        raise JuRuGalti(
            e.line, e.col,
            "to_json() cannot write a {} — JSON holds null, booleans, numbers, "
            "text, lists and dicts".format(_typename(v)), kind="type")

    def _bi_to_json(self, e, env):
        v = self.eval(e.args[0], env)
        self._json_check(v, e, set(), 1)
        try:
            text = json.dumps(v, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as err:
            raise JuRuGalti(
                e.line, e.col,
                "to_json() could not write this value — {}".format(err),
                kind="value")
        if len(text.encode("utf-8")) > self.MAX_FILE_BYTES:
            raise JuRuGalti(
                e.line, e.col,
                "to_json() produced too much text — the limit is 10 MB",
                kind="value")
        return text

    @staticmethod
    def _reject_json_constant(value):
        raise ValueError(value)

    def _bi_from_json(self, e, env):
        text = self.eval(e.args[0], env)
        if not isinstance(text, str):
            raise JuRuGalti(e.line, e.col,
                            "from_json() needs JSON text — got: {}".format(
                                display(text)), kind="type")
        size = len(text.encode("utf-8"))
        if size > self.MAX_FILE_BYTES:
            raise JuRuGalti(
                e.line, e.col,
                "from_json() text is too big ({}; the limit is 10 MB)".format(
                    self._bytes_text(size)), kind="value")
        try:
            data = json.loads(text, parse_constant=self._reject_json_constant)
        except json.JSONDecodeError as err:
            msg = err.msg or "the text is not valid JSON"
            msg = msg[0].lower() + msg[1:]
            raise JuRuGalti(
                e.line, e.col,
                "from_json() could not read the text — {} at line {} "
                "column {}".format(msg, err.lineno, err.colno), kind="value")
        except RecursionError:
            raise JuRuGalti(
                e.line, e.col,
                "from_json() found a value nested too deeply — the limit is "
                "{} levels".format(self.MAX_JSON_DEPTH), kind="value")
        except ValueError:
            raise JuRuGalti(
                e.line, e.col,
                "from_json() cannot read NaN or Infinity — JSON numbers must "
                "be finite", kind="value")
        stack = [(data, 1)]
        while stack:
            value, level = stack.pop()
            if isinstance(value, str):
                if _has_lone_surrogate(value):
                    raise JuRuGalti(
                        e.line, e.col,
                        "from_json() found an unpaired surrogate escape — "
                        "JSON text cannot hold half of a surrogate pair",
                        kind="value")
            elif isinstance(value, float):
                if not math.isfinite(value):
                    raise JuRuGalti(
                        e.line, e.col,
                        "from_json() cannot read NaN or Infinity — JSON "
                        "numbers must be finite", kind="value")
            elif isinstance(value, list):
                if level > self.MAX_JSON_DEPTH:
                    raise JuRuGalti(
                        e.line, e.col,
                        "from_json() found a value nested too deeply — the "
                        "limit is {} levels".format(self.MAX_JSON_DEPTH),
                        kind="value")
                stack.extend((item, level + 1) for item in value)
            elif isinstance(value, dict):
                if level > self.MAX_JSON_DEPTH:
                    raise JuRuGalti(
                        e.line, e.col,
                        "from_json() found a value nested too deeply — the "
                        "limit is {} levels".format(self.MAX_JSON_DEPTH),
                        kind="value")
                for key in value.keys():
                    if _has_lone_surrogate(key):
                        raise JuRuGalti(
                            e.line, e.col,
                            "from_json() found an unpaired surrogate escape — "
                            "JSON text cannot hold half of a surrogate pair",
                            kind="value")
                stack.extend((item, level + 1) for item in value.values())
        return data

    def _bi_format(self, e, env):
        template = self.eval(e.args[0], env)
        if not isinstance(template, str):
            raise JuRuGalti(e.line, e.col,
                            "format() needs text — got: {}".format(
                                display(template)))
        values = [self.eval(a, env) for a in e.args[1:]]
        return _format_text(template, values, e.line, e.col)

    def _bi_set_of(self, e, env):
        lst = self.eval(e.args[0], env)
        if not isinstance(lst, list):
            raise JuRuGalti(e.line, e.col,
                            "set_of() needs a list — got: {}".format(display(lst)))
        return SetV(lst)

    def _set_pair(self, e, env, name):
        a = self.eval(e.args[0], env)
        b = self.eval(e.args[1], env)
        if not isinstance(a, SetV) or not isinstance(b, SetV):
            raise JuRuGalti(e.line, e.col,
                            "{}() needs two sets — got: {} and {} "
                            "(build one with set_of([...]))".format(
                                name, _typename(a), _typename(b)))
        return a, b

    def _bi_union(self, e, env):
        a, b = self._set_pair(e, env, "union")
        out = SetV(a.items)
        for x in b.items:
            out.add(x)
        return out

    def _bi_intersect(self, e, env):
        a, b = self._set_pair(e, env, "intersect")
        out = SetV()
        for x in a.items:
            if b.has(x):
                out.add(x)
        return out

    def _bi_difference(self, e, env):
        a, b = self._set_pair(e, env, "difference")
        out = SetV()
        for x in a.items:
            if not b.has(x):
                out.add(x)
        return out

    def _make_builtin_call(self):
        """name → handler, straight from the registry (single source)."""
        return {
            "ask": self._bi_ask,
            "len": self._bi_len,
            "int": self._bi_int,
            "float": self._bi_float,
            "upper": self._bi_upper,
            "lower": self._bi_lower,
            "str": self._bi_str,
            "push": self._bi_push,
            "pop": self._bi_pop,
            "sum": self._bi_sum,
            "min": self._bi_min,
            "max": self._bi_max,
            "split": self._bi_split,
            "join": self._bi_join,
            "trim": self._bi_trim,
            "replace": self._bi_replace,
            "abs": self._bi_abs,
            "round": self._bi_round,
            "random": self._bi_random,
            "sqrt": self._bi_sqrt,
            "sorted": self._bi_sorted,
            "reverse": self._bi_reverse,
            "find": self._bi_find,
            "keys": self._bi_keys,
            "values": self._bi_values,
            "count": self._bi_count,
            "pow": self._bi_pow,
            "type": self._bi_type,
            "help": self._bi_help,
            "sleep": self._bi_sleep,
            "insert": self._bi_insert,
            "remove_at": self._bi_remove_at,
            "clear": self._bi_clear,
            "extend": self._bi_extend,
            "unique": self._bi_unique,
            "delete": self._bi_delete,
            "items": self._bi_items,
            "merge": self._bi_merge,
            "index_of": self._bi_index_of,
            "starts_with": self._bi_starts_with,
            "ends_with": self._bi_ends_with,
            "ord": self._bi_ord,
            "chr": self._bi_chr,
            "set_of": self._bi_set_of,
            "union": self._bi_union,
            "intersect": self._bi_intersect,
            "difference": self._bi_difference,
            "fail": self._bi_fail,
            "format": self._bi_format,
            "pad_left": self._bi_pad_left,
            "pad_right": self._bi_pad_right,
            "center": self._bi_center,
            "split_lines": self._bi_split_lines,
            "join_lines": self._bi_join_lines,
            "read_file": self._bi_read_file,
            "write_file": self._bi_write_file,
            "append_file": self._bi_append_file,
            "read_lines": self._bi_read_lines,
            "write_lines": self._bi_write_lines,
            "file_exists": self._bi_file_exists,
            "file_size": self._bi_file_size,
            "delete_file": self._bi_delete_file,
            "list_dir": self._bi_list_dir,
            "make_dir": self._bi_make_dir,
            "delete_dir": self._bi_delete_dir,
            "to_json": self._bi_to_json,
            "from_json": self._bi_from_json,
        }


def run_source(src):
    """Run JuRu source (text). Output comes through print()."""
    Interpreter().run(parse_source(src))
