"""JuRu Language — Step 2+: Parser (tokens → AST)
================================================

JuRu = easy + secure language.

Parser's job: build an AST (Abstract Syntax Tree) from the lexer's tokens.
The interpreter runs this tree, so every node remembers its place
(line/col) — error messages come from there.

Some SEMANTIC checks also happen here (a light version of step 3):
- 'break' / 'continue' only inside a loop (caught at parse time)
- 'return' only inside a func (caught at parse time)

How to run:
    python3 parser.py file.jr   # show the AST tree
"""

from .lexer import (
    Lexer, JuRuGalti, KEYWORDS,
    NUMBER, TEXT, NAME, KEYWORD, OPERATOR, NEWLINE, EOF,
)

# ------------------------------------------------------------------ AST nodes


class Node:
    """Every AST node knows its place (line, col)."""

    _fields = ()

    def __init__(self, line, col, *args):
        self.line = line
        self.col = col
        for name, val in zip(self._fields, args):
            setattr(self, name, val)
        for name in self._fields[len(args):]:   # optional fields stay None
            setattr(self, name, None)

    def __repr__(self):
        return dump(self)


class Program(Node):  _fields = ("stmts",)
class Num(Node):      _fields = ("value",)                  # "10", "3.14"
class Text(Node):     _fields = ("value",)                  # raw string
class Bool(Node):     _fields = ("value",)                  # true/false
class Null(Node):     _fields = ()                          # null
class Name(Node):     _fields = ("id",)
class ListLit(Node):  _fields = ("items",)                  # [1, 2, 3]
class DictLit(Node):  _fields = ("keys", "values")          # {"name": 5} — keys/values are parallel lists
class BinOp(Node):    _fields = ("op", "left", "right")     # + - * / % == < in and or...
class UnaryOp(Node):  _fields = ("op", "operand")           # - + not
class Call(Node):     _fields = ("name", "args", "callee")  # add(1, 2) — or callee (utils.add(1, 2))
class Index(Node):    _fields = ("seq", "idx", "idx_end", "is_slice", "idx_step")  # nums[0], nums[1:3], nums[1:7:2]
class Member(Node):   _fields = ("seq", "name")             # utils.double, d.name
class Assign(Node):   _fields = ("name", "value", "op")     # x = 5 — op is "+"/"-"/... when written x += e
class SetIndex(Node): _fields = ("seq", "idx", "value", "op")  # nums[0] = 5 — op for nums[0] += 5
class ExprSt(Node):   _fields = ("expr",)                   # a bare expression line
class Say(Node):      _fields = ("args",)                   # say(...)
class If(Node):       _fields = ("cond", "then", "orelse")  # if / else if / else
class While(Node):    _fields = ("cond", "body")            # while
class For(Node):      _fields = ("var", "start", "end", "body", "iter")  # for i from 1 to 10 / for x in items
class FuncDef(Node):  _fields = ("name", "params", "body")  # func f(a) { ... }
class Return(Node):   _fields = ("value",)                  # return [expr]
class Import(Node):   _fields = ("path", "module")          # import "utils.jr"
class Break(Node):    _fields = ()                          # break
class Continue(Node): _fields = ()                          # continue


def _join(items):
    if not items:
        return ""
    return " " + " ".join(dump(x) for x in items)


def dump(node):
    """Show the AST as an S-expression string (for tests + debugging)."""
    if isinstance(node, Program):
        return "(program{})".format(_join(node.stmts))
    if isinstance(node, Num):
        return "(num {})".format(node.value)
    if isinstance(node, Text):
        return "(text {})".format(node.value)
    if isinstance(node, Bool):
        return "(bool {})".format("true" if node.value else "false")
    if isinstance(node, Null):
        return "(null)"
    if isinstance(node, Name):
        return "(name {})".format(node.id)
    if isinstance(node, ListLit):
        return "(list{})".format(_join(node.items))
    if isinstance(node, BinOp):
        return "({} {} {})".format(node.op, dump(node.left), dump(node.right))
    if isinstance(node, UnaryOp):
        return "({} {})".format(node.op, dump(node.operand))
    if isinstance(node, Call):
        if node.callee is not None:                       # utils.add(1, 2)
            return "(call {}{})".format(dump(node.callee), _join(node.args))
        return "(call {}{})".format(node.name, _join(node.args))
    if isinstance(node, Index):
        if node.is_slice:                                 # nums[1:3]
            def _slice_part(x):
                return "(null)" if x is None else dump(x)
            if node.idx_step is not None:                 # nums[1:7:2]
                return "(slice-step {} {} {} {})".format(
                    dump(node.seq), _slice_part(node.idx),
                    _slice_part(node.idx_end), dump(node.idx_step))
            return "(slice {} {} {})".format(
                dump(node.seq), _slice_part(node.idx), _slice_part(node.idx_end))
        return "(index {} {})".format(dump(node.seq), dump(node.idx))
    if isinstance(node, Member):
        return "(member {} {})".format(dump(node.seq), node.name)
    if isinstance(node, DictLit):
        pairs = _join_flat(
            [kv for pair in zip(node.keys, node.values) for kv in pair])
        return "(dict{})".format(pairs)
    if isinstance(node, Assign):
        if node.op is not None:                           # x += e
            return "(augassign {} {} {})".format(node.op, node.name, dump(node.value))
        return "(assign {} {})".format(node.name, dump(node.value))
    if isinstance(node, SetIndex):
        if node.op is not None:                           # xs[i] += e
            return "(augsetindex {} {} {} {})".format(
                node.op, dump(node.seq), dump(node.idx), dump(node.value))
        return "(setindex {} {} {})".format(
            dump(node.seq), dump(node.idx), dump(node.value))
    if isinstance(node, ExprSt):
        return "(expr {})".format(dump(node.expr))
    if isinstance(node, Say):
        return "(say{})".format(_join(node.args))
    if isinstance(node, If):
        if node.orelse:
            if isinstance(node.orelse[0], If):          # else if (elif)
                orelse = " (else {})".format(dump(node.orelse[0]))
            else:                                        # else { ... }
                orelse = " (else (then{}))".format(_join(node.orelse))
        else:
            orelse = ""
        return "(if {} (then{}){})".format(dump(node.cond), _join(node.then), orelse)
    if isinstance(node, While):
        return "(while {} (then{}))".format(dump(node.cond), _join(node.body))
    if isinstance(node, For):
        if node.iter is not None:                         # for x in items
            return "(for-in {} {} (then{}))".format(
                node.var, dump(node.iter), _join(node.body))
        return "(for {} {} {} (then{}))".format(
            node.var, dump(node.start), dump(node.end), _join(node.body))
    if isinstance(node, FuncDef):
        return "(func {} (params{}) (then{}))".format(
            node.name, _join_plain(node.params), _join(node.body))
    if isinstance(node, Return):
        return "(return{})".format((" " + dump(node.value)) if node.value is not None else "")
    if isinstance(node, Break):
        return "(break)"
    if isinstance(node, Continue):
        return "(continue)"
    if isinstance(node, Import):
        return '(import "{}" {})'.format(node.path, node.module)
    raise TypeError("dump: unknown node " + repr(node))


def _join_flat(items):
    """Like _join but items may be nodes (dumped) or plain strings."""
    if not items:
        return ""
    parts = []
    for x in items:
        parts.append(dump(x) if isinstance(x, Node) else str(x))
    return " " + " ".join(parts)


def _join_plain(words):
    if not words:
        return ""
    return " " + " ".join(words)


def _stem(path):
    """'lib/helpers.jr' → 'helpers' (for error messages)."""
    base = path.replace("\\", "/").split("/")[-1]
    return base[:-3] if base.endswith(".jr") else base


def _module_name(path):
    """The name the module gets: stem of the file, must be a valid JuRu name."""
    stem = _stem(path)
    if not stem or not (stem[0].isalpha() and stem[0].isascii() or stem[0] == "_"):
        return None
    if not all(ch.isalnum() and ch.isascii() or ch == "_" for ch in stem):
        return None
    return stem


# ------------------------------------------------------------------ parser

COMP_OPS = {"==", "!=", "<=", ">=", "<", ">"}
AUG_OPS = {"+=", "-=", "*=", "/=", "%="}   # augmented assignment: x += e


class Parser:
    """Tokens → AST (recursive descent)."""

    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0
        self.loop_depth = 0    # break/continue only inside loops (checked here)
        self.func_depth = 0    # return only inside funcs

    # ---------- stream helpers ----------
    def cur(self):
        return self.toks[self.i]

    def peek(self, ahead=1):
        j = self.i + ahead
        return self.toks[j] if j < len(self.toks) else self.toks[-1]

    def next(self):
        t = self.toks[self.i]
        if self.i < len(self.toks) - 1:   # never step past EOF
            self.i += 1
        return t

    def at(self, type_, value=None):
        t = self.cur()
        return t.type == type_ and (value is None or t.value == value)

    def skip_nl(self):
        while self.at(NEWLINE):
            self.i += 1

    # ---------- friendly errors ----------
    def _found(self, t):
        if t.type == EOF:
            return "the end of the code"
        if t.type == NEWLINE:
            return "a new line"
        return "'{}'".format(t.value)

    def expect_op(self, op, hint=""):
        if self.at(OPERATOR, op):
            return self.next()
        t = self.cur()
        extra = (" " + hint) if hint else ""
        if t.type == OPERATOR and t.value == "=":
            raise JuRuGalti(t.line, t.col,
                            "expected '{}' here — and '=' is not it; for comparison write '=='{}".format(op, extra))
        raise JuRuGalti(t.line, t.col,
                        "expected '{}' here, found: {}{}".format(op, self._found(t), extra))

    def expect_kw(self, word, hint=""):
        if self.at(KEYWORD, word):
            return self.next()
        t = self.cur()
        extra = (" " + hint) if hint else ""
        raise JuRuGalti(t.line, t.col,
                        "expected '{}' here, found: {}{}".format(word, self._found(t), extra))

    def expect_name(self, hint=""):
        if self.at(NAME):
            return self.next()
        t = self.cur()
        extra = (" " + hint) if hint else ""
        if t.type == KEYWORD:
            raise JuRuGalti(t.line, t.col, "'{}' is a keyword — it cannot be a name{}".format(t.value, extra))
        raise JuRuGalti(t.line, t.col,
                        "expected a name here, found: {}{}".format(self._found(t), extra))

    def _after_stmt(self, start_tok):
        """After every statement: a new line, '}', or end — otherwise an error."""
        t = self.cur()
        if t.type in (NEWLINE, EOF) or (t.type == OPERATOR and t.value == "}"):
            return
        if t.type == KEYWORD and t.value == "else":
            raise JuRuGalti(t.line, t.col, "'else' needs a matching 'if' before it")
        raise JuRuGalti(t.line, t.col,
                        "one statement per line — after '{}' found: {}; write the next one on a new line".format(
                            start_tok.value, self._found(t)))

    # ---------- program / statements ----------
    def parse(self):
        stmts = []
        first = self.cur()
        self.skip_nl()
        while not self.at(EOF):
            stmts.append(self.statement())
            self.skip_nl()
        return Program(first.line, first.col, stmts)

    def statement(self):
        t = self.cur()
        if t.type == KEYWORD:
            kw = t.value
            if kw == "if":
                return self.if_stmt()
            if kw == "while":
                return self.while_stmt()
            if kw == "for":
                return self.for_stmt()
            if kw == "func":
                return self.func_stmt()
            if kw == "import":
                return self.import_stmt()
            if kw == "return":
                return self.return_stmt()
            if kw == "say":
                return self.say_stmt()
            if kw in ("break", "continue"):
                if self.loop_depth == 0:
                    raise JuRuGalti(t.line, t.col,
                                    "'{}' only works inside a loop (for / while)".format(kw))
                tok = self.next()
                self._after_stmt(tok)
                return (Break if kw == "break" else Continue)(tok.line, tok.col)
            if kw in ("true", "false", "null", "not"):
                return self.expr_stmt()      # a value-statement: 'true', 'not x'...
            if kw == "else":
                raise JuRuGalti(t.line, t.col, "'else' needs a matching 'if' before it (else if ... or else { ...)")
            if kw in ("and", "or"):
                raise JuRuGalti(t.line, t.col, "'{}' joins two things — write the things first".format(kw))
            if kw in ("from", "to"):
                raise JuRuGalti(t.line, t.col, "'{}' only works inside 'for i from 1 to 10'".format(kw))
            if kw in ("in", "import", "and", "or"):
                raise JuRuGalti(t.line, t.col, "'{}' cannot start a statement".format(kw))
            raise JuRuGalti(t.line, t.col, "'{}' cannot start a statement".format(kw))
        if t.type == NAME:
            return self.name_stmt()
        if t.type == OPERATOR and t.value == "{":
            raise JuRuGalti(t.line, t.col,
                            "'{' cannot start a statement — a dict needs a home: write 'data = { ... }'")
        if t.type == OPERATOR and t.value == "}":
            raise JuRuGalti(t.line, t.col, "'}' cannot appear without a '{'")
        if t.type in (NUMBER, TEXT) or (t.type == OPERATOR and t.value in ("(", "[", "-", "+")):
            return self.expr_stmt()
        raise JuRuGalti(t.line, t.col, "a statement cannot start here, found: {}".format(self._found(t)))

    def name_stmt(self):
        name_tok = self.cur()
        nxt = self.peek(1)
        if nxt.type == OPERATOR and nxt.value == "=":
            self.next()                  # name
            self.next()                  # =
            self.skip_nl()               # x =\n 5 is allowed
            val = self.expr()
            self._after_stmt(name_tok)
            return Assign(name_tok.line, name_tok.col, name_tok.value, val)
        if nxt.type == OPERATOR and nxt.value in AUG_OPS:
            # x += e — the shorthand for x = x + e. The Assign remembers the
            # op; the interpreter reads the old value and applies it once.
            self.next()                  # name
            op_tok = self.next()         # += -= *= /= %=
            self.skip_nl()
            val = self.expr()
            self._after_stmt(name_tok)
            return Assign(name_tok.line, name_tok.col, name_tok.value, val,
                          op_tok.value[0])
        expr = self.expr()
        t2 = self.cur()
        if t2.type == OPERATOR and (t2.value == "=" or t2.value in AUG_OPS):
            self.next()                  # = or an augmented op (+= ...)
            self.skip_nl()
            val = self.expr()
            self._after_stmt(name_tok)
            if isinstance(expr, Index):
                if t2.value == "=":
                    return SetIndex(expr.line, expr.col, expr.seq, expr.idx, val)
                # xs[i] += e — the shorthand for xs[i] = xs[i] + e
                return SetIndex(expr.line, expr.col, expr.seq, expr.idx, val,
                                t2.value[0])
            if isinstance(expr, Member):
                raise JuRuGalti(name_tok.line, name_tok.col,
                                "assign to a dict with 'data[\"key\"] = value' — 'data.key = value' does not work")
            raise JuRuGalti(name_tok.line, name_tok.col,
                            "write plain 'name = value' or 'list[index] = value' — '{}' cannot follow an expression".format(t2.value))
        self._after_stmt(name_tok)
        return ExprSt(name_tok.line, name_tok.col, expr)

    def expr_stmt(self):
        start = self.cur()
        e = self.expr()
        self._after_stmt(start)
        return ExprSt(start.line, start.col, e)

    def if_stmt(self):
        kw = self.next()
        cond = self.expr()
        then = self.block()
        orelse = []
        save = self.i
        self.skip_nl()
        if self.at(KEYWORD, "else"):
            self.next()
            if self.at(KEYWORD, "if"):
                orelse = [self.if_stmt()]            # else if = elif
            else:
                orelse = self.block()                # else { ... }
        else:
            self.i = save   # no 'else' — give the newline back (next statement can run)
        self._after_stmt(kw)
        return If(kw.line, kw.col, cond, then, orelse)

    def while_stmt(self):
        kw = self.next()
        cond = self.expr()
        self.loop_depth += 1
        body = self.block()
        self.loop_depth -= 1
        self._after_stmt(kw)
        return While(kw.line, kw.col, cond, body)

    def for_stmt(self):
        kw = self.next()
        var = self.expect_name("the for loop needs a variable, like 'for i from 1 to 10'")
        if self.at(KEYWORD, "in"):                     # for x in items { ... }
            self.next()
            it = self.expr()
            self.loop_depth += 1
            body = self.block()
            self.loop_depth -= 1
            self._after_stmt(kw)
            return For(kw.line, kw.col, var.value, None, None, body, it)
        self.expect_kw("from", "did you forget 'from'? — 'for i from 1 to 10'")
        start = self.expr()          # for i FROM 1 TO 5 { ... }
        self.expect_kw("to", "did you forget 'to'? — 'for i from 1 to 10'")
        end = self.expr()
        self.loop_depth += 1
        body = self.block()
        self.loop_depth -= 1
        self._after_stmt(kw)
        return For(kw.line, kw.col, var.value, start, end, body)

    def func_stmt(self):
        kw = self.next()
        name = self.expect_name("a func needs a name, like 'func add(a, b)'")
        self.expect_op("(", "functions are written 'name(args)'")
        params = []
        self.skip_nl()
        if not self.at(OPERATOR, ")"):
            while True:
                p = self.expect_name("a parameter needs a name (like 'a')")
                params.append(p.value)
                self.skip_nl()
                if self.at(OPERATOR, ","):
                    self.next()
                    self.skip_nl()
                    continue
                break
        self.expect_op(")")
        self.func_depth += 1
        body = self.block()
        self.func_depth -= 1
        self._after_stmt(kw)
        return FuncDef(kw.line, kw.col, name.value, params, body)

    def import_stmt(self):
        kw = self.next()
        t = self.cur()
        if t.type != TEXT:
            raise JuRuGalti(t.line, t.col,
                            'import needs the file in double quotes — like import "utils.jr"')
        self.next()
        path = t.value
        if not path.endswith(".jr"):
            raise JuRuGalti(t.line, t.col,
                            "JuRu files end with '.jr' — you gave: '{}'".format(path))
        module = _module_name(path)
        if module is None:
            raise JuRuGalti(
                t.line, t.col,
                "the file '{}' gives the module name '{}' — that is not a valid name; "
                "rename the file (letters, digits, _)".format(path, _stem(path)))
        if module in KEYWORDS:
            raise JuRuGalti(
                t.line, t.col,
                "the file '{}' would create the module '{}' — that is a keyword; "
                "rename the file".format(path, module))
        self._after_stmt(kw)
        return Import(kw.line, kw.col, path, module)

    def return_stmt(self):
        if self.func_depth == 0:
            t = self.cur()
            raise JuRuGalti(t.line, t.col, "'return' only works inside a func")
        kw = self.next()
        t = self.cur()
        if t.type == NEWLINE or t.type == EOF or (t.type == OPERATOR and t.value == "}"):
            self._after_stmt(kw)
            return Return(kw.line, kw.col, None)
        val = self.expr()
        self._after_stmt(kw)
        return Return(kw.line, kw.col, val)

    def say_stmt(self):
        kw = self.next()
        self.expect_op("(", "write say(...) — put what to show inside the brackets")
        args = self._args(")")
        self._after_stmt(kw)
        return Say(kw.line, kw.col, args)

    def block(self):
        self.expect_op("{", "(blocks start with '{' and end with '}' — no indentation)")
        stmts = []
        self.skip_nl()
        while not self.at(OPERATOR, "}"):
            if self.at(EOF):
                raise JuRuGalti(self.cur().line, self.cur().col,
                                "'}' is missing — the block is never closed")
            if self.at(KEYWORD, "else"):
                t = self.cur()
                raise JuRuGalti(t.line, t.col,
                                "close '}' first — 'else' comes after the block")
            stmts.append(self.statement())
            self.skip_nl()
        self.next()   # take the }
        return stmts

    # ---------- expressions ----------
    # precedence (loose to tight): or > and > compare > add > mul > unary > postfix > atom

    def expr(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.at(KEYWORD, "or"):
            op = self.next()
            self.skip_nl()
            left = BinOp(op.line, op.col, "or", left, self.and_expr())
        return left

    def and_expr(self):
        left = self.compare()
        while self.at(KEYWORD, "and"):
            op = self.next()
            self.skip_nl()
            left = BinOp(op.line, op.col, "and", left, self.compare())
        return left

    def compare(self):
        left = self.add()
        t = self.cur()
        op_value = None
        if t.type == OPERATOR and t.value in COMP_OPS:
            op_value = t.value
            op = self.next()
        elif t.type == KEYWORD and t.value == "in":
            op_value = "in"
            op = self.next()
        elif t.type == KEYWORD and t.value == "not" \
                and self.peek(1).type == KEYWORD and self.peek(1).value == "in":
            op_value = "not in"
            op = self.next()          # not
            self.next()               # in
        else:
            return left
        self.skip_nl()
        right = self.add()
        nxt = self.cur()
        if nxt.type == OPERATOR and nxt.value in COMP_OPS:
            raise JuRuGalti(nxt.line, nxt.col,
                            "only one '{}' per comparison — chains ('1 < 2 < 3') do not work; join with 'and'".format(nxt.value))
        if nxt.type == KEYWORD and nxt.value == "in" or \
                (nxt.type == KEYWORD and nxt.value == "not"
                 and self.peek(1).type == KEYWORD and self.peek(1).value == "in"):
            raise JuRuGalti(nxt.line, nxt.col,
                            "one comparison per line — chains like 'a in b in c' do not work")
        return BinOp(op.line, op.col, op_value, left, right)

    def add(self):
        left = self.mul()
        while self.at(OPERATOR, "+") or self.at(OPERATOR, "-"):
            op = self.next()
            self.skip_nl()               # a new line after an operator = continuation
            left = BinOp(op.line, op.col, op.value, left, self.mul())
        return left

    def mul(self):
        left = self.unary()
        while self.at(OPERATOR, "*") or self.at(OPERATOR, "/") or self.at(OPERATOR, "%"):
            op = self.next()
            self.skip_nl()
            left = BinOp(op.line, op.col, op.value, left, self.unary())
        return left

    def unary(self):
        t = self.cur()
        if t.type == OPERATOR and t.value in ("-", "+"):
            self.next()
            return UnaryOp(t.line, t.col, t.value, self.unary())
        if t.type == KEYWORD and t.value == "not":
            self.next()
            return UnaryOp(t.line, t.col, "not", self.unary())
        return self.postfix()

    def postfix(self):
        node = self.atom()
        while True:
            t = self.cur()
            if t.type == OPERATOR and t.value == "(":
                if isinstance(node, Name):
                    self.next()
                    node = Call(t.line, t.col, node.id, self._args(")"))
                elif isinstance(node, Member):
                    self.next()                       # utils.double(...)
                    node = Call(t.line, t.col, node.name, self._args(")"), node)
                else:
                    raise JuRuGalti(t.line, t.col,
                                    "'(' needs a name before it — only 'name(...)' calls work")
            elif t.type == OPERATOR and t.value == "[":
                self.next()
                self.skip_nl()
                first = None
                if not self.at(OPERATOR, ":"):
                    first = self.expr()
                    self.skip_nl()
                if self.at(OPERATOR, ":"):                 # nums[1:3] / nums[:2] / nums[1:] / nums[1:7:2]
                    self.next()
                    self.skip_nl()
                    second = None
                    if not self.at(OPERATOR, ":") and not self.at(OPERATOR, "]"):
                        second = self.expr()
                        self.skip_nl()
                    step = None
                    if self.at(OPERATOR, ":"):             # a third part: the step
                        self.next()
                        self.skip_nl()
                        if not self.at(OPERATOR, "]"):
                            step = self.expr()
                            self.skip_nl()
                    self.expect_op("]", "a slice ends with ']' — like nums[1:3]")
                    node = Index(t.line, t.col, node, first, second, True, step)
                else:
                    if first is None:
                        raise JuRuGalti(t.line, t.col,
                                        "expected a value inside the brackets — like nums[0]")
                    self.expect_op("]")
                    node = Index(t.line, t.col, node, first)
            elif t.type == OPERATOR and t.value == ".":
                self.next()
                name_tok = self.expect_name(
                    "after '.', write the member name — like utils.double")
                node = Member(t.line, t.col, node, name_tok.value)
            else:
                return node

    def _args(self, closer):
        """Inside (a, b, c) / [a, b] — new lines are allowed."""
        self.skip_nl()
        args = []
        if self.at(OPERATOR, closer):
            self.next()
            return args
        while True:
            args.append(self.expr())
            self.skip_nl()
            t = self.cur()
            if t.type == OPERATOR and t.value == ",":
                self.next()
                self.skip_nl()
                continue
            if t.type == OPERATOR and t.value == closer:
                self.next()
                return args
            raise JuRuGalti(t.line, t.col,
                            "expected ',' or '{}' here, found: {}".format(closer, self._found(t)))

    def atom(self):
        t = self.cur()
        if t.type == NUMBER:
            self.next()
            return Num(t.line, t.col, t.value)
        if t.type == TEXT:
            self.next()
            return Text(t.line, t.col, t.value)
        if t.type == NAME:
            self.next()
            return Name(t.line, t.col, t.value)
        if t.type == KEYWORD:
            kw = t.value
            if kw in ("true", "false"):
                self.next()
                return Bool(t.line, t.col, kw == "true")
            if kw == "null":
                self.next()
                return Null(t.line, t.col)
            if kw == "say":
                raise JuRuGalti(t.line, t.col,
                                "say is a statement — not a value; write 'say(...)' on its own line")
            raise JuRuGalti(t.line, t.col,
                            "'{}' is a keyword — it cannot be used as a name or a value".format(kw))
        if t.type == OPERATOR and t.value == "(":
            self.next()
            self.skip_nl()
            inner = self.expr()
            self.skip_nl()
            self.expect_op(")")
            return inner
        if t.type == OPERATOR and t.value == "[":
            self.next()
            return ListLit(t.line, t.col, self._args("]"))
        if t.type == OPERATOR and t.value == "{":
            self.next()                                   # dict literal
            self.skip_nl()
            keys, values = [], []
            if not self.at(OPERATOR, "}"):
                while True:
                    k = self.expr()
                    self.skip_nl()
                    self.expect_op(
                        ":",
                        'in a dict, a key and value are joined by ":" — like {"name": 5}')
                    self.skip_nl()
                    v = self.expr()
                    keys.append(k)
                    values.append(v)
                    self.skip_nl()
                    if self.at(OPERATOR, ","):
                        self.next()
                        self.skip_nl()
                        continue
                    break
            self.expect_op("}", "a dict ends with '}'")
            return DictLit(t.line, t.col, keys, values)
        if t.type == EOF:
            raise JuRuGalti(t.line, t.col,
                            "the code ended — a value was expected here")
        raise JuRuGalti(t.line, t.col,
                        "expected a value here, found: {}".format(self._found(t)))


# ------------------------------------------------------------------ helpers

def parse_source(src):
    """Text → tokens → AST (in one call)."""
    return Parser(Lexer(src).tokenize()).parse()


def parse_file(path):
    with open(path, encoding="utf-8") as f:
        return parse_source(f.read())


def _run_cli():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 parser.py file.jr")
        sys.exit(1)
    try:
        tree = parse_file(sys.argv[1])
    except JuRuGalti as err:
        print(str(err))
        sys.exit(1)
    print(dump(tree))


if __name__ == "__main__":
    _run_cli()
