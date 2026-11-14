"""JuRu MEGA tests — steps 1 to 5, all together, in the most brutal way.

Covers:
- all 17 keywords in ONE program
- the flagship school report (exact output)
- loop stress (20,000 iterations), recursion (factorial 15, fibo 20)
- control-flow torture (nested for / while / if / break / continue)
- text torture and list torture with the new stdlib
- in-place list reverse through SetIndex
- every example file through the real CLI and the checker
- the four error layers (lex / parse / check / runtime) through the CLI
- proof that the checker runs BEFORE the interpreter
- the REPL under mixed fire
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from juru.lexer import JuRuGalti
from juru.checker import check_source
from test_repl import run_repl, lines_after_prompts

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


def run_capture(src):
    """Run source text through checker + interpreter, return stdout."""
    import contextlib, io
    from juru.interpreter import Interpreter
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree)
    return buf.getvalue()


def example_files():
    folder = os.path.join(HERE, "examples")
    return sorted(f for f in os.listdir(folder) if f.endswith(".jr"))


# ------------------------------------------------------------------ 17 keywords
KEYWORDS = ["say", "if", "else", "while", "for", "from", "to", "break",
            "continue", "func", "return", "true", "false", "null",
            "and", "or", "not"]

ALL_KEYWORDS_SRC = '''
func probe(n) {
    if n == 0 {
        return null
    } else {
        return true
    }
}
seen = null
for i from 1 to 3 {
    while i == 2 {
        break
    }
    if i == 1 {
        continue
    }
    if i == 3 and probe(i) {
        seen = i
    }
}
say(probe(5) and not (seen == null) or false)
'''


def t_all_17_keywords():
    for kw in KEYWORDS:
        assert re.search(r"\b" + kw + r"\b", ALL_KEYWORDS_SRC), "missing: " + kw
    out = run_capture(ALL_KEYWORDS_SRC)
    assert out == "true\n", "output: " + repr(out)


# ------------------------------------------------------------------ mega demo
MEGA_EXPECTED = (
    "CLASS REPORT\n"
    "Aarav -> 78 (grade C)\n"
    "Diya -> 76 (grade C)\n"
    "Esha -> 100 (grade A)\n"
    "Kabir -> 64 (grade D)\n"
    "Ria -> 91 (grade A)\n"
    "class average: 81.8\n"
    "-- ranking --\n"
    "1. Esha 100\n"
    "2. Ria 91\n"
    "3. Aarav 78\n"
    "4. Diya 76\n"
    "5. Kabir 64\n"
    "topper: Esha\n"
    "gold star for ESHA!\n"
    "-- histogram --\n"
    "A | ##\n"
    "B | \n"
    "C | ##\n"
    "D | #\n"
)


def t_mega_checker():
    path = os.path.join(HERE, "examples", "mega_demo.jr")
    with open(path, encoding="utf-8") as f:
        check_source(f.read())


def t_mega_demo_exact():
    path = os.path.join(HERE, "examples", "mega_demo.jr")
    with open(path, encoding="utf-8") as f:
        out = run_capture(f.read())
    assert out == MEGA_EXPECTED, "\n--- got ---\n" + out + "\n--- want ---\n" + MEGA_EXPECTED


# ------------------------------------------------------------------ stress
def t_loop_stress():
    out = run_capture(
        "total = 0\n"
        "for i from 1 to 20000 {\n"
        "    total = total + i\n"
        "}\n"
        "say(total)\n"
    )
    assert out == "200010000\n", out


def t_recursion_stress():
    out = run_capture(
        "func factorial(n) {\n"
        "    if n <= 1 {\n"
        "        return 1\n"
        "    }\n"
        "    return n * factorial(n - 1)\n"
        "}\n"
        "func fibo(n) {\n"
        "    if n <= 2 {\n"
        "        return 1\n"
        "    }\n"
        "    return fibo(n - 1) + fibo(n - 2)\n"
        "}\n"
        "say(factorial(15))\n"
        "say(fibo(20))\n"
    )
    assert out == "1307674368000\n6765\n", out


def t_control_flow_torture():
    """35 rounds, 3 skipped by continue -> 32 hits, with break inside nesting."""
    out = run_capture(
        "hits = 0\n"
        "for i from 1 to 35 {\n"
        "    if i == 3 or i == 7 or i == 11 {\n"
        "        continue\n"
        "    }\n"
        "    while true {\n"
        "        break\n"
        "    }\n"
        "    for j from 1 to 3 {\n"
        "        if j == 2 {\n"
        "            break\n"
        "        }\n"
        "        hits = hits + 1\n"
        "    }\n"
        "}\n"
        "say(hits)\n"
    )
    assert out == "32\n", out


# ------------------------------------------------------------------ stdlib torture
def t_text_torture():
    out = run_capture(
        'word = "abcde"\n'
        "up = upper(word)\n"
        "low = lower(up)\n"
        "say(up + \"|\" + low + \"|\" + len(word))\n"
    )
    assert out == "ABCDE|abcde|5\n", out


def t_list_torture():
    out = run_capture(
        "data = []\n"
        "for i from 1 to 10 {\n"
        "    push(data, (i * 7) % 10)\n"
        "}\n"
        "say(data)\n"
        "say(sum(data))\n"
        "say(min(data[0], data[1]))\n"
        "say(max(data[2], data[3]))\n"
    )
    assert out == (
        "[7, 4, 1, 8, 5, 2, 9, 6, 3, 0]\n"
        "45\n"
        "4\n"
        "8\n"
    ), out


def t_inplace_reverse():
    out = run_capture(
        "seq = []\n"
        "for i from 0 to 9 {\n"
        "    push(seq, (i * 3) % 10)\n"
        "}\n"
        "left = 0\n"
        "right = len(seq) - 1\n"
        "while left < right {\n"
        "    temp = seq[left]\n"
        "    seq[left] = seq[right]\n"
        "    seq[right] = temp\n"
        "    left = left + 1\n"
        "    right = right - 1\n"
        "}\n"
        "say(seq)\n"
    )
    assert out == "[7, 4, 1, 8, 5, 2, 9, 6, 3, 0]\n", out


# ------------------------------------------------------------------ every example
def t_all_examples_cli():
    files = example_files()
    assert len(files) >= 11, "expected 11+ examples, got: " + str(files)
    for name in files:
        proc = subprocess.run(
            [sys.executable, "juru.py", os.path.join("examples", name)],
            capture_output=True, text=True, cwd=HERE,
        )
        assert proc.returncode == 0, "{} failed: {}".format(name, proc.stdout)


def t_checker_on_all_examples():
    from juru.checker import check_file
    for name in example_files():
        check_file(os.path.join(HERE, "examples", name))  # must not raise


# ------------------------------------------------------------------ error layers
def cli_err(src, fragment):
    path = os.path.join(HERE, ".tmp_mega.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        proc = subprocess.run(
            [sys.executable, "juru.py", path], capture_output=True, text=True, cwd=HERE)
        assert proc.returncode == 1, "should fail: " + src
        assert fragment in proc.stdout, proc.stdout
    finally:
        os.remove(path)


def t_error_layers_cli():
    # 1) lexer
    cli_err('say("unterminated', 'missing closing "')
    # 2) parser
    cli_err("x = 1 +", "the code ended — a value was expected here")
    # 3) checker
    cli_err("say(ghost)", "'ghost' was not found")
    # 4) interpreter
    cli_err("y = 1\ny = y / 0\n", "cannot divide by zero (x / 0)")


def t_checker_before_runtime():
    """The semantic error must be reported BEFORE a single line runs."""
    path = os.path.join(HERE, ".tmp_mega.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write("y = 1\ny = y / 0\nsay(ghost)\n")   # runtime bomb on line 2...
    try:
        proc = subprocess.run(
            [sys.executable, "juru.py", path], capture_output=True, text=True, cwd=HERE)
        assert proc.returncode == 1
        # ...but the CHECKER error wins
        assert "'ghost' was not found" in proc.stdout, proc.stdout
        assert "divide by zero" not in proc.stdout, proc.stdout
    finally:
        os.remove(path)


# ------------------------------------------------------------------ REPL torture
def t_repl_torture():
    out = lines_after_prompts(run_repl([
        "nums = [5, 3]",
        "push(nums, 8)",
        "sum(nums)",
        "max(3, 9)",
        "func sq(n) { return n * n }",
        "sq(7)",
        "1 / 0",
        "2 + 2",
        "nosuchname",
        'upper("final")',
        "exit",
    ]))
    assert "=> [5, 3, 8]" in out, out
    assert "=> 16" in out, out
    assert "=> 9" in out, out
    assert "=> 49" in out, out
    assert any("cannot divide by zero" in ln for ln in out), out
    assert "=> 4" in out, out
    assert any("'nosuchname' was not found" in ln for ln in out), out
    assert "=> FINAL" in out, out


ALL = [
    ("all 17 keywords in one program -> true", t_all_17_keywords),
    ("mega_demo passes the checker", t_mega_checker),
    ("mega_demo exact school report", t_mega_demo_exact),
    ("loop stress: 20000 iterations", t_loop_stress),
    ("recursion: factorial(15) + fibo(20)", t_recursion_stress),
    ("control-flow torture (35 - 3 = 32 hits)", t_control_flow_torture),
    ("text torture ABCDE|abcde|5", t_text_torture),
    ("list torture + sum/min/max", t_list_torture),
    ("in-place reverse via SetIndex", t_inplace_reverse),
    ("every example through juru.py (exit 0)", t_all_examples_cli),
    ("checker approves every example", t_checker_on_all_examples),
    ("four error layers through the CLI", t_error_layers_cli),
    ("checker runs BEFORE the interpreter", t_checker_before_runtime),
    ("REPL under mixed fire", t_repl_torture),
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
