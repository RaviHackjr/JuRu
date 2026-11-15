"""JuRu error rendering (Step 17) — show the line, point at the exact column.

Python shows the offending line with a caret. JuRu does too:

    JuRu Error (line 2, col 10): index 7 is out of range — this list has 3 items (0 to 2)
        nums[7]
            ^

Rules:
  - the message line itself NEVER changes (str(err) stays byte-identical)
  - the context lines are display only: the CLI, the REPL and any host
    that has the source text use render(); everything else keeps str(err)
  - if the source is unavailable or the line is out of range, render()
    falls back to the plain message — it can never show a WRONG line
"""

INDENT = "    "


def render(err, src=None):
    """str(err) plus the offending line and a caret, when possible."""
    text = str(err)
    source = src
    path = getattr(err, "source_file", None)
    if path:                                  # the error came from a module
        try:
            with open(path, encoding="utf-8") as f:
                source = f.read()
        except OSError:
            return text
    if not source:
        return text
    lines = source.splitlines()
    if not (1 <= err.line <= len(lines)):
        return text
    raw = lines[err.line - 1]
    stripped = raw.strip()
    if not stripped:
        return text
    indent = len(raw) - len(raw.lstrip())
    caret = max(err.col - 1 - indent, 0)      # col is 1-based over the raw line
    return "{}\n{}{}\n{}{}^".format(text, INDENT, stripped, INDENT, " " * caret)
