"""JuRu Step 16 tests — sleep() and the bare-`juru` REPL.

  sleep(seconds)  pause the program — with every guard imaginable:
                  numbers only, no negatives, max 30s per call,
                  max 120s per run (runaway loops cannot hide in sleep)
  juru (no args)  opens the REPL — exactly like bare `python`
"""
import io
import contextlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti
from juru.checker import check_source, BUILTIN_ARITY, BUILTIN_HINT
from juru.interpreter import Interpreter
from juru.version import VERSION

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


def run(src, one=None, total=None):
    """Run with (optionally) shrunk sleep caps so guards are test-fast."""
    tree = check_source(src)
    interp = Interpreter()
    if one is not None:
        interp.MAX_SLEEP_ONE = one
    if total is not None:
        interp.MAX_SLEEP_TOTAL = total
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(tree, base_dir=HERE)
    return buf.getvalue()


def cli(args, input_text=None, cwd=HERE):
    return subprocess.run(
        [sys.executable, JURU] + args,
        input=input_text, capture_output=True, text=True, cwd=cwd, timeout=120,
    )


# ------------------------------------------------------------------ sleep
def t_sleep_works():
    assert run("sleep(0.01)\nsay(\"awake\")") == "awake\n"
    assert run("sleep(0)\nsay(\"no wait\")") == "no wait\n"
    assert run("sleep(0.01 + 0.01)\nsay(\"sum works\")") == "sum works\n"


def t_sleep_returns_null():
    assert run('say(type(sleep(0)))') == "null\n"


def t_sleep_needs_a_number():
    for bad in ('sleep("x")', 'sleep(true)', "sleep(null)", "sleep([1])"):
        try:
            run(bad)
        except JuRuGalti as err:
            assert err.message.startswith("sleep() needs a number of seconds"), err.message
        else:
            raise AssertionError("accepted: " + bad)


def t_sleep_no_time_travel():
    try:
        run("sleep(-1)")
    except JuRuGalti as err:
        assert err.message == (
            "sleep() cannot go back in time — seconds cannot be negative (got: -1)"
        ), err.message
    else:
        raise AssertionError("negative sleep accepted")


def t_sleep_max_one_call():
    try:
        run("sleep(31)")
    except JuRuGalti as err:
        assert err.message == (
            "sleep() takes at most 30 seconds at a time (got: 31)"
        ), err.message
    else:
        raise AssertionError("over-long sleep accepted")
    # the guard is `>` (not `>=`): a sleep EXACTLY at the cap is allowed —
    # tested with a shrunk cap so no test ever really sleeps long
    assert run("sleep(0.05)\nsay(\"ok\")", one=0.05) == "ok\n"
    try:
        run("sleep(0.06)", one=0.05)
    except JuRuGalti as err:
        assert "takes at most 0.05 seconds at a time" in err.message, err.message
    else:
        raise AssertionError("over-cap sleep accepted with shrunk cap")


def t_sleep_total_budget():
    """Runaway loops cannot hide inside sleep() — the run has a sleep budget."""
    try:
        run("sleep(0.04)\nsleep(0.04)", one=30.0, total=0.05)
    except JuRuGalti as err:
        assert "slept more than" in err.message and "in total" in err.message, err.message
    else:
        raise AssertionError("total budget not enforced")
    # the first call under the budget still works
    assert run("sleep(0.04)\nsay(\"ok\")", one=30.0, total=0.05) == "ok\n"


def t_sleep_budget_inside_a_loop():
    src = ("i = 0\n"
           "while true {\n"
           "    i = i + 1\n"
           "    sleep(0.02)\n"
           "}\n")
    try:
        run(src, one=30.0, total=0.05)
    except JuRuGalti as err:
        assert "slept more than" in err.message, err.message
    else:
        raise AssertionError("infinite sleeping loop ran forever")


def t_sleep_arity_and_mirror():
    try:
        run("sleep()")
    except JuRuGalti as err:
        assert err.message == "sleep(seconds) takes exactly 1 argument", err.message
    try:
        run("sleep(1, 2)")
    except JuRuGalti as err:
        assert err.message == "sleep(seconds) takes exactly 1 argument", err.message
    assert BUILTIN_ARITY["sleep"] == (1, 1)
    assert BUILTIN_HINT["sleep"] == "sleep(seconds) takes exactly 1 argument"


# ------------------------------------------------------------------ bare juru
def t_no_args_opens_repl():
    proc = cli([], input_text="say(pow(2, 3))\nexit\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.startswith("JuRu {} (".format(VERSION)), proc.stdout
    assert "juru> 8" in proc.stdout, proc.stdout


def t_no_args_repl_env_persists():
    proc = cli([], input_text="total = 40\ntotal + 2\nexit\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "=> 42" in proc.stdout, proc.stdout


def t_help_flag_still_prints_usage():
    for flag in ("--help", "-h"):
        proc = cli([flag])
        assert proc.returncode == 0, proc.stdout
        assert "--new NAME" in proc.stdout, proc.stdout


def t_version_flag_untouched():
    proc = cli(["--version"])
    assert proc.stdout.strip() == "JuRu " + VERSION, proc.stdout


def t_sleep_in_a_game_round():
    """The real use: pacing a guessing game round."""
    src = ('say("round starts")\n'
           "sleep(0.01)\n"
           'say("you guessed!")\n')
    assert run(src) == "round starts\nyou guessed!\n"


ALL = [
    ("sleep works (and sleep(0))", t_sleep_works),
    ("sleep returns null", t_sleep_returns_null),
    ("sleep needs a number", t_sleep_needs_a_number),
    ("sleep: no time travel", t_sleep_no_time_travel),
    ("sleep: max 30s per call", t_sleep_max_one_call),
    ("sleep: total budget per run", t_sleep_total_budget),
    ("sleep: budget stops runaway loops", t_sleep_budget_inside_a_loop),
    ("sleep: arity + mirror messages", t_sleep_arity_and_mirror),
    ("bare juru opens the REPL", t_no_args_opens_repl),
    ("bare juru REPL keeps the environment", t_no_args_repl_env_persists),
    ("--help/-h still print usage", t_help_flag_still_prints_usage),
    ("--version untouched", t_version_flag_untouched),
    ("sleep in a real game round", t_sleep_in_a_game_round),
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
