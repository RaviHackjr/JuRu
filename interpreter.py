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
import os
import random as _random

from lexer import JuRuGalti
from parser import (
    Program, Num, Text, Bool, Null, Name, ListLit, DictLit, BinOp, UnaryOp,
    Call, Index, Member, Assign, SetIndex, ExprSt, Say, If, While, For,
    FuncDef, Return, Import, Break, Continue,
    parse_source,
)
from checker import check_source, did_you_mean

BUILTINS = ("ask", "len", "int", "upper", "lower", "str", "push", "sum", "min", "max",
            "split", "join", "trim", "replace", "abs", "round", "random", "sqrt",
            "sorted", "reverse", "find", "keys", "values", "count")
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
    if isinstance(v, str):
        return v
    if isinstance(v, FuncValue):
        return "<func {}>".format(v.name)
    if isinstance(v, ModuleValue):
        return "<module {}>".format(v.name)
    return str(v)


class Interpreter:
    def __init__(self):
        self._modules = {}    # absolute path → ModuleValue (each file runs once)
        self._loading = []    # (path, base dir) stack — import loops die here

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
            env.vars[st.name] = self.eval(st.value, env)
            return

        if isinstance(st, SetIndex):
            seq = self.eval(st.seq, env)
            if isinstance(seq, dict):
                key = self._check_key(self.eval(st.idx, env), st.idx)
                seq[key] = self.eval(st.value, env)
                return
            if not isinstance(seq, list):
                raise JuRuGalti(st.line, st.col,
                                "only lists and dicts support item assignment (this is {})".format(_typename(seq)))
            idx = self._check_index(seq, st.idx, env)
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
        else:
            raise JuRuGalti(st.line, st.col,
                            "'for x in ...' needs a list, text, or dict — got: {}".format(display(seq)))
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
    def _check_key(key, node):
        """Dict keys are text or whole numbers — everything else is a mistake."""
        if isinstance(key, (str, int)) and not isinstance(key, bool):
            return key
        raise JuRuGalti(node.line, node.col,
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
            raise JuRuGalti(err.line, err.col,
                            "in '{}': {}".format(st.path, err.message))
        menv = Env()                              # a module sees nothing of the importer
        self._loading.append((path, os.path.dirname(path)))
        try:
            self._exec_block(tree.stmts, menv)
        except JuRuGalti as err:
            raise JuRuGalti(err.line, err.col,
                            "in '{}': {}".format(st.path, err.message))
        finally:
            self._loading.pop()
        mod = ModuleValue(st.module, menv, path)
        self._modules[path] = mod
        env.vars[st.module] = mod

    def _slice_bound(self, seq, node, env, default, label):
        if node is None:
            return default
        v = self.eval(node, env)
        if isinstance(v, bool) or not isinstance(v, int):
            raise JuRuGalti(node.line, node.col,
                            "the slice {} must be a whole number (int) — got: {}".format(label, display(v)))
        if v < 0:
            raise JuRuGalti(node.line, node.col,
                            "the slice {} cannot be negative — slices do not count backwards".format(label, display(v)))
        return min(v, len(seq))

    def _member(self, seq, e):
        if isinstance(seq, dict):
            if e.name in seq:
                return seq[e.name]
            self._missing_key(e.name, seq, e)
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
                start = self._slice_bound(seq, e.idx, env, 0, "start")
                end = self._slice_bound(seq, e.idx_end, env, len(seq), "end")
                return seq[start:end]
            if isinstance(seq, dict):
                key = self._check_key(self.eval(e.idx, env), e.idx)
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
                key = self._check_key(self.eval(k_node, env), k_node)
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
        if not 0 <= idx < n:
            raise JuRuGalti(idx_node.line, idx_node.col,
                            "index {} is out of range — this {} has {} items (0 to {})".format(
                                idx, _typename(seq), n, n - 1))
        return idx

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

        if op in ("in", "not in"):
            found = self._membership(left, right, e)
            return found if op == "in" else not found

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                if isinstance(left, (list, FuncValue)) or isinstance(right, (list, FuncValue)):
                    raise JuRuGalti(e.line, e.col,
                                    "a list or func cannot be joined with text")
                return display(left) + display(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if _is_num(left) and _is_num(right):
                return left + right
            raise JuRuGalti(e.line, e.col,
                            "cannot use '+' on {} and {}".format(_typename(left), _typename(right)))

        if op in ("-", "*", "/", "%"):
            if op == "*" and isinstance(left, str):
                if isinstance(right, int) and not isinstance(right, bool) and right >= 0:
                    if len(left) * right > MAX_LOOP_STEPS:
                        raise JuRuGalti(e.line, e.col,
                                        "text * {} would be too big — text cannot grow "
                                        "over 10,000,000 characters".format(display(right)))
                    return left * right
                raise JuRuGalti(e.line, e.col,
                                "text * number needs a whole number (0 or more) — got: {}".format(
                                    display(right)))
            if not (_is_num(left) and _is_num(right)):
                raise JuRuGalti(e.line, e.col,
                                "'{}' only works on numbers — got {} and {}".format(
                                    op, _typename(left), _typename(right)))
            if op == "/" and right == 0:
                raise JuRuGalti(e.line, e.col, "cannot divide by zero (x / 0)")
            if op == "%" and right == 0:
                raise JuRuGalti(e.line, e.col, "cannot use '%' with zero (x % 0)")
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
                raise JuRuGalti(e.line, e.col,
                                "'{}' cannot compare {} and {} — different worlds".format(
                                    op, _typename(left), _typename(right)))
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right

        raise JuRuGalti(e.line, e.col, "unknown operator: " + op)

    def _membership(self, item, container, e):
        """x in list / x in text / key in dict (and the 'not in' twin)."""
        if isinstance(container, list):
            return any(self._equals(item, x) for x in container)
        if isinstance(container, str):
            if not isinstance(item, str):
                raise JuRuGalti(e.line, e.col,
                                "'in' on text needs text on the left — got: {}".format(display(item)))
            return item in container
        if isinstance(container, dict):
            key = self._check_key(item, e)
            return key in container
        raise JuRuGalti(e.line, e.col,
                        "'in' needs a list, text, or dict on the right — got: {}".format(display(container)))

    @staticmethod
    def _equals(a, b):
        # true != 1 (different categories), but 1 == 1.0 (same number family)
        if isinstance(a, bool) != isinstance(b, bool):
            return False
        if _is_num(a) and _is_num(b):
            return a == b
        if type(a) is not type(b):
            return False
        return a == b

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
        try:
            self._exec_block(func.body, cenv)
        except ReturnSignal as r:
            return r.value
        except RecursionError:
            raise JuRuGalti(e.line, e.col,
                            "recursion went too deep — it never stops")
        return None

    def _builtin(self, e, env):
        name = e.name
        if name == "ask":
            if len(e.args) > 1:
                raise JuRuGalti(e.line, e.col, "ask(prompt) takes at most 1 argument")
            prompt = display(self.eval(e.args[0], env)) if e.args else ""
            try:
                return builtins.input(prompt)
            except EOFError:
                raise JuRuGalti(
                    e.line, e.col,
                    "ask() could not read any more input — the program was "
                    "waiting for an answer and the input ended")
        if name == "len":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "len(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if isinstance(v, (str, list, dict)):
                return len(v)
            raise JuRuGalti(e.line, e.col,
                            "'{}' has no length — only text, lists and dicts do".format(_typename(v)))
        # ---- Step 5 stdlib: upper / lower / str / push / sum / min / max ----
        if name == "upper":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "upper(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, str):
                raise JuRuGalti(e.line, e.col,
                                "upper() needs text — got: {}".format(display(v)))
            return v.upper()
        if name == "lower":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "lower(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, str):
                raise JuRuGalti(e.line, e.col,
                                "lower() needs text — got: {}".format(display(v)))
            return v.lower()
        if name == "str":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "str(x) takes exactly 1 argument")
            return display(self.eval(e.args[0], env))
        if name == "push":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "push(list, item) takes exactly 2 arguments")
            lst = self.eval(e.args[0], env)
            if not isinstance(lst, list):
                raise JuRuGalti(e.line, e.col,
                                "push() needs a list — got: {}".format(display(lst)))
            lst.append(self.eval(e.args[1], env))
            return lst
        if name == "sum":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "sum(list) takes exactly 1 argument")
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
        if name == "min":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "min(a, b) takes exactly 2 arguments")
            a = self.eval(e.args[0], env)
            b = self.eval(e.args[1], env)
            if not (_is_num(a) and _is_num(b)):
                raise JuRuGalti(e.line, e.col,
                                "min() needs numbers — got {} and {}".format(
                                    _typename(a), _typename(b)))
            return a if a <= b else b
        if name == "max":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "max(a, b) takes exactly 2 arguments")
            a = self.eval(e.args[0], env)
            b = self.eval(e.args[1], env)
            if not (_is_num(a) and _is_num(b)):
                raise JuRuGalti(e.line, e.col,
                                "max() needs numbers — got {} and {}".format(
                                    _typename(a), _typename(b)))
            return a if a >= b else b
        # ---- Step 6 stdlib: split / join / trim / replace / abs / round / random / sqrt ----
        if name == "split":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "split(text, separator) takes exactly 2 arguments")
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
        if name == "join":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "join(list, separator) takes exactly 2 arguments")
            lst = self.eval(e.args[0], env)
            sep = self.eval(e.args[1], env)
            if not isinstance(lst, list):
                raise JuRuGalti(e.line, e.col,
                                "join() needs a list — got: {}".format(display(lst)))
            if not isinstance(sep, str):
                raise JuRuGalti(e.line, e.col,
                                "the join separator must be text — got: {}".format(display(sep)))
            return sep.join(display(x) for x in lst)
        if name == "trim":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "trim(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, str):
                raise JuRuGalti(e.line, e.col,
                                "trim() needs text — got: {}".format(display(v)))
            return v.strip()
        if name == "replace":
            if len(e.args) != 3:
                raise JuRuGalti(e.line, e.col, "replace(text, old, new) takes exactly 3 arguments")
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
        if name == "abs":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "abs(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not _is_num(v):
                raise JuRuGalti(e.line, e.col,
                                "abs() needs a number — got: {}".format(display(v)))
            return abs(v)
        if name == "round":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "round(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not _is_num(v):
                raise JuRuGalti(e.line, e.col,
                                "round() needs a number — got: {}".format(display(v)))
            if isinstance(v, int):
                return v
            # half away from zero: 2.5 → 3, -2.5 → -3 (no surprises)
            return int(v + 0.5) if v >= 0 else int(v - 0.5)
        if name == "random":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "random(low, high) takes exactly 2 arguments")
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
        if name == "sqrt":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "sqrt(x) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not _is_num(v):
                raise JuRuGalti(e.line, e.col,
                                "sqrt() needs a number — got: {}".format(display(v)))
            if v < 0:
                raise JuRuGalti(e.line, e.col,
                                "sqrt({}) — a negative number has no square root".format(display(v)))
            return v ** 0.5
        # ---- Step 9 stdlib: sorted / reverse / find / keys / values / count ----
        if name == "sorted":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "sorted(list) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, list):
                raise JuRuGalti(e.line, e.col,
                                "sorted() needs a list — got: {}".format(display(v)))
            if not all(_is_num(x) for x in v) and not all(isinstance(x, str) for x in v):
                raise JuRuGalti(e.line, e.col,
                                "sorted() needs a list of only numbers or only text — got: {}".format(display(v)))
            return sorted(v)          # a NEW list — the original stays as it is
        if name == "reverse":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "reverse(list) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, list):
                raise JuRuGalti(e.line, e.col,
                                "reverse() needs a list — got: {}".format(display(v)))
            return list(reversed(v))  # a NEW list — the original stays as it is
        if name == "find":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "find(list, item) takes exactly 2 arguments")
            lst = self.eval(e.args[0], env)
            target = self.eval(e.args[1], env)
            if not isinstance(lst, list):
                raise JuRuGalti(e.line, e.col,
                                "find() needs a list first — got: {}".format(display(lst)))
            for i, x in enumerate(lst):
                if self._equals(x, target):
                    return i
            return -1                 # not found — a plain -1, easy to check
        if name == "keys":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "keys(dict) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, dict):
                raise JuRuGalti(e.line, e.col,
                                "keys() needs a dict — got: {}".format(display(v)))
            return list(v.keys())
        if name == "values":
            if len(e.args) != 1:
                raise JuRuGalti(e.line, e.col, "values(dict) takes exactly 1 argument")
            v = self.eval(e.args[0], env)
            if not isinstance(v, dict):
                raise JuRuGalti(e.line, e.col,
                                "values() needs a dict — got: {}".format(display(v)))
            return list(v.values())
        if name == "count":
            if len(e.args) != 2:
                raise JuRuGalti(e.line, e.col, "count(list, item) takes exactly 2 arguments")
            lst = self.eval(e.args[0], env)
            target = self.eval(e.args[1], env)
            if not isinstance(lst, list):
                raise JuRuGalti(e.line, e.col,
                                "count() needs a list first — got: {}".format(display(lst)))
            return sum(1 for x in lst if self._equals(x, target))
        # int(x)
        if len(e.args) != 1:
            raise JuRuGalti(e.line, e.col, "int(x) takes exactly 1 argument")
        v = self.eval(e.args[0], env)
        if isinstance(v, bool) or v is None or isinstance(v, (list, dict, FuncValue)):
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


def run_source(src):
    """Run JuRu source (text). Output comes through print()."""
    Interpreter().run(parse_source(src))
