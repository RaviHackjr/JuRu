"""JuRu Step 5 tests — the REPL (persistent env, echo, error recovery).

Every test talks to the real process: python3 repl.py < stdin.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
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


def run_repl(lines):
    proc = subprocess.run(
        [sys.executable, "repl.py"],
        input="\n".join(lines) + "\n",
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    return proc.stdout


def lines_after_prompts(out):
    """Strip the prompts from each line: 'jruru> jruru> X' -> 'X'."""
    cleaned = []
    for ln in out.splitlines():
        ln = ln.replace("......> ", "").replace("jruru> ", "")
        if ln in ("jruru>", "......>"):
            ln = ""
        if ln:
            cleaned.append(ln)
    return cleaned


def t_banner_and_prompt():
    out = run_repl(["exit"])
    assert "JuRu 1.3 REPL" in out, out
    assert out.count("jruru> ") >= 1, out


def t_echo_arithmetic():
    out = lines_after_prompts(run_repl(["1 + 2", "(2 + 3) * 2", "exit"]))
    assert "=> 3" in out, out
    assert "=> 10" in out, out


def t_assign_no_echo_then_use():
    out = lines_after_prompts(run_repl(["x = 5", "x * 2", "exit"]))
    # assignment must NOT echo, the read must see the stored value
    assert "=> 5" not in out, out
    assert "=> 10" in out, out


def t_say_no_echo():
    out = lines_after_prompts(run_repl(['say("hi")', '2 * 2', "exit"]))
    assert "hi" in out, out
    assert "=> 4" in out, out
    # say printed directly: the line before '=> 4' is exactly 'hi', not 'hi => ...'
    assert not any("=>" in ln for ln in out if ln.startswith("hi")), out


def t_error_recovery():
    out = lines_after_prompts(run_repl(["1 / 0", "1 + 1", "exit"]))
    assert any("cannot divide by zero" in ln for ln in out), out
    assert "=> 2" in out, out  # the session survived


def t_funcs_across_lines():
    out = lines_after_prompts(run_repl([
        "func double(n) { return n * 2 }",
        "double(4)",
        "double(21)",
        "exit",
    ]))
    assert "=> 8" in out, out
    assert "=> 42" in out, out


def t_stdlib_in_repl():
    out = lines_after_prompts(run_repl([
        "nums = [1]",
        "push(nums, 2)",
        'upper("ok")',
        "sum([3, 4])",
        "exit",
    ]))
    assert "=> [1, 2]" in out, out
    assert "=> OK" in out, out
    assert "=> 7" in out, out


def t_reserved_and_checker_enforced():
    out = lines_after_prompts(run_repl([
        "len = 5",
        "min = 1",
        "y + 1",
        "len([1, 2])",
        "exit",
    ]))
    assert any("'len' is reserved (builtin)" in ln for ln in out), out
    assert any("'min' is reserved (builtin)" in ln for ln in out), out
    assert any("'y' was not found" in ln for ln in out), out
    assert "=> 2" in out, out  # builtins still callable


def t_eof_exit():
    """No 'exit' line — Ctrl-D (EOF) closes the session cleanly."""
    proc = subprocess.run(
        [sys.executable, "repl.py"],
        input="7 * 6\n", capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "=> 42" in proc.stdout, proc.stdout


def t_exit_quits_immediately():
    out = run_repl(["exit", "1 + 1"])
    assert "=> 2" not in out, out  # nothing runs after exit
    out = run_repl(["quit", "1 + 1"])
    assert "=> 2" not in out, out


ALL = [
    ("banner + prompt", t_banner_and_prompt),
    ("echo arithmetic", t_echo_arithmetic),
    ("assign: no echo, value usable", t_assign_no_echo_then_use),
    ("say prints, no echo", t_say_no_echo),
    ("error recovery survives", t_error_recovery),
    ("funcs persist across lines", t_funcs_across_lines),
    ("stdlib inside the REPL", t_stdlib_in_repl),
    ("checker + reserved enforced", t_reserved_and_checker_enforced),
    ("Ctrl-D (EOF) exits cleanly", t_eof_exit),
    ("exit / quit stop at once", t_exit_quits_immediately),
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
