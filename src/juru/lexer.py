"""JuRu Language — Step 1: Lexer
==============================

JuRu = easy + secure language (easier than Python, safe like Rust).

Lexer's job: break source code (plain text) into TOKENS.
The parser (step 2) builds an AST tree from these tokens.

How to run:
    python3 lexer.py            # read code from stdin
    python3 lexer.py file.jr    # read code from a file
"""

import unicodedata

# ---------- Token types ----------
NUMBER = "NUMBER"      # 10, 3.14
TEXT = "TEXT"          # "hello"
NAME = "NAME"          # name, age
KEYWORD = "KEYWORD"    # say, if, while, ...
OPERATOR = "OPERATOR"  # + = == { ...
NEWLINE = "NEWLINE"    # statement ends
EOF = "EOF"            # code ends

# JuRu keywords — 19 total! (Python has 35+)
# Idea: code = a conversation in plain English.
KEYWORDS = {
    "say",       # output — like print
    "if", "else",
    "while",
    "for", "from", "to", "in",
    "break", "continue",
    "func", "return",
    "true", "false", "null",
    "and", "or", "not",
    "import",    # modules — Step 7
}

SINGLE_OPS = set("+-*/%=<>(){}[],:.")
DOUBLE_OPS = {"==", "!=", "<=", ">="}
ASCII_DIGITS = set("0123456789")
SPACES = (" ", "\t", "\r")


class JuRuGalti(Exception):
    """A JuRu error — human language, with the exact place (line/col)."""

    def __init__(self, line, col, message):
        self.line = line
        self.col = col
        self.message = message
        self.source_file = None   # set when the error came from an imported module
        super().__init__("JuRu Error (line {}, col {}): {}".format(line, col, message))


class Token:
    """One small piece: type + value + place (line, col)."""

    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return "{}({!r}) @{}:{}".format(self.type, self.value, self.line, self.col)


class Lexer:
    """Source code (text) → tokens."""

    def __init__(self, source):
        self.src = source
        self.n = len(source)
        self.pos = 0
        self.line = 1
        self.col = 1

    # ---------- small helpers ----------
    def _peek(self, ahead=0):
        i = self.pos + ahead
        return self.src[i] if i < self.n else ""

    def _step(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    # ---------- main loop ----------
    def tokenize(self):
        tokens = []
        while self.pos < self.n:
            line, col = self.line, self.col
            ch = self._peek()

            if ch in SPACES:           # spaces do not matter
                self._step()

            elif ch == "\n":
                self._step()
                # many empty lines in a row = just one NEWLINE
                if tokens and tokens[-1].type != NEWLINE:
                    tokens.append(Token(NEWLINE, "\n", line, col))

            elif ch == "#":            # comment: skip until end of line
                while self._peek() not in ("", "\n"):
                    self._step()

            elif ch in ASCII_DIGITS:
                tokens.append(self._number())

            elif ch == '"':
                tokens.append(self._text())

            elif ch.isalpha() or ch == "_":
                tokens.append(self._name())

            elif ch == "." and self._peek(1) in ASCII_DIGITS:
                raise JuRuGalti(
                    line, col,
                    "decimal numbers are written '0.5' — no leading '.'",
                )

            else:
                tok = self._operator()
                if tok is None:
                    raise JuRuGalti(line, col, self._unknown_hint(ch))
                tokens.append(tok)

        tokens.append(Token(EOF, "<end>", self.line, self.col))
        return tokens

    # ---------- readers ----------
    def _number(self):
        line, col = self.line, self.col
        start = self.pos
        while self._peek() in ASCII_DIGITS:
            self._step()
        if self._peek() == ".":
            self._step()  # take the dot
            if not self._peek() in ASCII_DIGITS:
                raise JuRuGalti(
                    line, self.col - 1,
                    "digits are needed after the dot, like 1.5 — a lone '.' does nothing?",
                )
            while self._peek() in ASCII_DIGITS:
                self._step()
            if self._peek() == ".":
                raise JuRuGalti(
                    line, col,
                    "a number can have only one dot (like 1.5, 3.14)",
                )
        return Token(NUMBER, self.src[start:self.pos], line, col)

    def _text(self):
        line, col = self.line, self.col   # place of the opening quote
        self._step()                      # take the "
        chars = []
        while True:
            ch = self._peek()
            if ch in ("", "\n"):
                raise JuRuGalti(
                    line, col,
                    'missing closing " — text must be on one line',
                )
            self._step()
            if ch == '"':
                break
            if ch == "\\":
                esc = self._peek()
                if esc in ("", "\n"):
                    raise JuRuGalti(
                        self.line, self.col,
                        "something must come after \\ (like \\n, \\t)",
                    )
                self._step()
                if esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == '"':
                    chars.append('"')
                elif esc == "\\":
                    chars.append("\\")
                else:
                    raise JuRuGalti(
                        self.line, self.col - 1,
                        "I do not know the escape '\\{}' — only \\n, \\t, \\\" and \\\\ work".format(esc),
                    )
            else:
                chars.append(ch)
        return Token(TEXT, "".join(chars), line, col)

    def _name(self):
        line, col = self.line, self.col
        start = self.pos
        while self._name_char(self._peek()):
            self._step()
        word = self.src[start:self.pos]
        type_ = KEYWORD if word in KEYWORDS else NAME
        return Token(type_, word, line, col)

    @staticmethod
    def _name_char(ch):
        # letters / digits / underscore, plus combining marks (Devanagari
        # matras and friends) so words like 'नाम' read as one single name
        if ch == "":
            return False
        return ch.isalnum() or ch == "_" or unicodedata.category(ch).startswith("M")

    def _operator(self):
        line, col = self.line, self.col
        ch = self._peek()
        two = ch + (self._peek(1) or "")
        if two in DOUBLE_OPS:
            self._step()
            self._step()
            return Token(OPERATOR, two, line, col)
        if ch in SINGLE_OPS:
            self._step()
            return Token(OPERATOR, ch, line, col)
        return None

    @staticmethod
    def _unknown_hint(ch):
        if ch == "!":
            return "'!' alone does not work — write '!=' (not equal)"
        if ch == "&":
            return "use 'and' instead of '&'"
        if ch == "|":
            return "use 'or' instead of '|'"
        if ch == ";":
            return "no semicolons needed — one statement per line"
        if ch == "'":
            return 'text goes in double quotes "like this", not single quotes'
        return "'{}' — I do not understand this; remove it or write it correctly".format(ch)


def _run_cli():
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            src = f.read()
    else:
        src = sys.stdin.read()
    try:
        tokens = Lexer(src).tokenize()
    except JuRuGalti as err:
        print(str(err))
        sys.exit(1)
    for t in tokens:
        print(t)


if __name__ == "__main__":
    _run_cli()
