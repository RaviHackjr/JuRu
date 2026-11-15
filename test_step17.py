"""JuRu Step 17 tests — errors show the line and point at the column.

Python shows the offending line with a caret; JuRu does the same now,
in the CLI and the REPL. The rules enforced here:
  - the message line NEVER changes: str(err) is byte-identical, so the
    checker/interpreter mirror rule and every existing message keep holding
  - the caret is under the exact column (leading indentation is stripped)
  - module errors borrow the module's own file for their context
  - when the source is unknown or the line is out of range, the output is
    exactly the plain message — never a WRONG line, never a traceback
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti
from juru.checker import check_source
from juru.errfmt import render
from juru.interpreter import Interpreter

HERE = os.path.dirname(os.path.abspath(__file__))
JURU = os.path.join(HERE, "juru.py")
RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print("PASS  " + name)
    except AssertionError as e:
        RESULTS.append((name, False, "FAIL: " + str(e)))
        print("FAIL  " + name + " -> " + str(e))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False, "ERROR: " + repr(e)))
        print("ERROR " + name + " -> " + repr(e))


def run(src):
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=HERE)
    return buf.getvalue()


def catch(src):
    try:
        run(src)
    except JuRuGalti as err:
        return err
    raise AssertionError("expected an error: " + src)


def cli(args, input_text=None, cwd=None):
    return subprocess.run(
        [sys.executable, JURU] + args,
        input=input_text, capture_output=True, text=True,
        cwd=cwd or HERE, timeout=120,
    )


# ------------------------------------------------------------------ rendering
def t_message_line_never_changes():
    err = catch("say(1 / 0)")
    shown = render(err, "say(1 / 0)")
    assert shown.startswith(str(err)), shown
    assert str(err).endswith("divide by zero (x / 0)"), str(err)


def t_caret_points_at_the_column():
    err = catch("nums = [1, 2, 3]\nsay(nums[7])")
    shown = render(err, "nums = [1, 2, 3]\nsay(nums[7])")
    lines = shown.splitlines()
    assert len(lines) == 3, lines
    assert lines[1] == "    say(nums[7])", lines
    assert lines[2] == "    " + " " * 9 + "^", lines     # col 10 → 9 spaces


def t_caret_strips_leading_indent():
    src = ("nums = [1, 2, 3]\n"
           "if true {\n"
           "    say(nums[7])\n"
           "}\n")
    err = catch(src)
    shown = render(err, src)
    lines = shown.splitlines()
    assert lines[1] == "    say(nums[7])", lines          # indent stripped
    assert lines[2].count("^") == 1, lines
    assert lines[2].index("^") == lines[1].index("say(") + 9, lines


def t_render_never_shows_a_wrong_line():
    err = catch("say(1 / 0)")
    assert render(err, None) == str(err)                  # no source → plain
    assert render(err, "") == str(err)                    # empty → plain
    deep = catch("x = 1\nsay(1 / 0)")                     # error on line 2
    assert render(deep, "other = 1\n") == str(deep)       # line out of range
    blank = JuRuGalti(1, 1, "boom")
    assert render(blank, "\n\n") == str(blank)            # blank line → plain


def t_module_errors_borrow_the_module_file():
    d = tempfile.mkdtemp(prefix="juru_err_")
    with open(os.path.join(d, "lib.jr"), "w", encoding="utf-8") as f:
        f.write("say(ghost)\n")
    with open(os.path.join(d, "main.jr"), "w", encoding="utf-8") as f:
        f.write("x = 1\ny = 2\nz = 3\nimport \"lib.jr\"\n")
    proc = cli([os.path.join(d, "main.jr")], cwd=d)
    out = proc.stdout
    assert "in 'lib.jr': 'ghost' was not found" in out, out
    assert "    say(ghost)" in out, out                   # the MODULE's line...
    assert out.count("^") == 1, out                       # ...with one caret


def t_parse_errors_get_carets_too():
    d = tempfile.mkdtemp(prefix="juru_err_")
    path = os.path.join(d, "oops.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write('say("unclosed\nsay(1)\n')
    proc = cli([path], cwd=d)
    out = proc.stdout
    assert out.startswith("JuRu Error (line 1,"), out
    assert "    say(\"unclosed" in out, out
    assert out.count("^") == 1, out


def t_cli_never_tracebacks():
    d = tempfile.mkdtemp(prefix="juru_err_")
    path = os.path.join(d, "bad.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write("nums = [1]\nsay(nums[9])\n")
    proc = cli([path], cwd=d)
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr, proc.stderr
    assert proc.stdout.count("^") == 1, proc.stdout


def t_repl_shows_carets():
    proc = cli(["repl"], input_text="say(naame)\nexit\n")
    out = proc.stdout
    assert "'naame' was not found" in out, out
    assert "    say(naame)" in out, out
    assert out.count("^") == 1, out


def t_repl_multiline_error_context():
    proc = cli(["repl"],
               input_text="nums = [1, 2, 3]\n"
                          "for i from 1 to 2 {\n"
                          "say(i)\n"
                          "say(nums[5])\n"
                          "}\n"
                          "exit\n")
    out = proc.stdout
    assert "index 5 is out of range" in out, out
    assert "    say(nums[5])" in out, out
    assert out.count("^") == 1, out


def t_clean_programs_print_nothing_extra():
    assert run("say(1 + 1)") == "2\n"                     # success is untouched


ALL = [
    ("message line never changes", t_message_line_never_changes),
    ("caret points at the exact column", t_caret_points_at_the_column),
    ("caret strips leading indent", t_caret_strips_leading_indent),
    ("render never shows a wrong line", t_render_never_shows_a_wrong_line),
    ("module errors borrow the module file", t_module_errors_borrow_the_module_file),
    ("parse errors get carets too", t_parse_errors_get_carets_too),
    ("the CLI never leaks a traceback", t_cli_never_tracebacks),
    ("the REPL shows carets", t_repl_shows_carets),
    ("REPL multi-line blocks too", t_repl_multiline_error_context),
    ("clean programs print nothing extra", t_clean_programs_print_nothing_extra),
]

if __name__ == "__main__":
    for name, fn in ALL:
        check(name, fn)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    print("\n{}/{} tests passed".format(passed, len(RESULTS)))
    if failed:
        print("{} FAILED".format(failed))
        sys.exit(1)
