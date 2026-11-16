"""JuRu advanced tests — the 3 heavy programs of steps 1-4 (exact output).

Each program must:
1. pass the checker (step 3) with no semantic errors,
2. run through the interpreter (step 4) with EXACTLY the expected output,
3. run through the real CLI (python3 juru.py ...) and match again.
"""
import contextlib
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.checker import check_source
from juru.interpreter import Interpreter

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


def run_program(name):
    """examples/<name> -> checker -> interpreter -> captured stdout."""
    path = os.path.join(HERE, "examples", "test", name)
    with open(path, encoding="utf-8") as f:
        src = f.read()
    tree = check_source(src)  # must pass step 3
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree)  # step 4
    return buf.getvalue()


def expect_exact(name, expected):
    out = run_program(name)
    assert out == expected, "\n--- got ---\n{!r}\n--- want ---\n{!r}".format(out, expected)


# ------------------------------------------------------------------ expected
NUMBER_LAB = (
    "primes: 2 3 5 7 11 13 17 19 23 29 \n"
    "perfect: 6 28 \n"
    "reverse 1234 -> 4321\n"
    "reverse 7050 -> 507\n"
    "1221 is a number palindrome!\n"
    "gcd(462, 1071) = 21\n"
    "lcm(4, 6) = 12\n"
)

ALGO_LAB = (
    "sorted: [11, 12, 22, 25, 64]\n"
    "find 22 -> index 2\n"
    "find 99 -> index -1\n"
    "dedupe: [1, 2, 3, 4, 5]\n"
    "rle: a3b2c1\n"
    "longest: interpreter\n"
)

GAME_LAB = (
    "X | - | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "--- move 1: X -> row 0, col 0\n"
    "X | O | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "--- move 2: O -> row 0, col 1\n"
    "X | O | -\n"
    "---+---+---\n"
    "- | X | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "--- move 3: X -> row 1, col 1\n"
    "X | O | O\n"
    "---+---+---\n"
    "- | X | -\n"
    "---+---+---\n"
    "- | - | -\n"
    "--- move 4: O -> row 0, col 2\n"
    "X | O | O\n"
    "---+---+---\n"
    "- | X | -\n"
    "---+---+---\n"
    "- | - | X\n"
    "--- move 5: X -> row 2, col 2\n"
    "X WINS!\n"
    "\n"
    "A hits B for 12 -> B: 38\n"
    "B hits A for 15 -> A: 35\n"
    "A hits B for 9 -> B: 29\n"
    "B hits A for 20 -> A: 15\n"
    "A hits B for 7 -> B: 22\n"
    "B hits A for 11 -> A: 4\n"
    "A hits B for 30 -> B: -8\n"
    "A WINS THE ARENA!\n"
)


def line_of(name, i):
    """The i-th output line of a program (0-based)."""
    return run_program(name).splitlines()[i]


# ------------------------------------------------------------------ number_lab
def t_number_checker():
    run_program("number_lab.jr")  # must not raise


def t_number_exact():
    expect_exact("number_lab.jr", NUMBER_LAB)


def t_number_lines():
    assert line_of("number_lab.jr", 0) == "primes: 2 3 5 7 11 13 17 19 23 29 "
    assert line_of("number_lab.jr", 1) == "perfect: 6 28 "
    assert line_of("number_lab.jr", 4) == "1221 is a number palindrome!"
    assert line_of("number_lab.jr", 5) == "gcd(462, 1071) = 21"
    assert line_of("number_lab.jr", 6) == "lcm(4, 6) = 12"


# ------------------------------------------------------------------ algo_lab
def t_algo_checker():
    run_program("algo_lab.jr")


def t_algo_exact():
    expect_exact("algo_lab.jr", ALGO_LAB)


def t_algo_lines():
    lines = run_program("algo_lab.jr").splitlines()
    assert lines[0] == "sorted: [11, 12, 22, 25, 64]"
    assert lines[1] == "find 22 -> index 2"
    assert lines[2] == "find 99 -> index -1"
    assert lines[3] == "dedupe: [1, 2, 3, 4, 5]"
    assert lines[4] == "rle: a3b2c1"
    assert lines[5] == "longest: interpreter"


# ------------------------------------------------------------------ game_lab
def t_game_checker():
    run_program("game_lab.jr")


def t_game_exact():
    expect_exact("game_lab.jr", GAME_LAB)


def t_game_win():
    lines = run_program("game_lab.jr").splitlines()
    assert "--- move 5: X -> row 2, col 2" in lines
    assert "X WINS!" in lines
    # the diagonal X at (0,0) (1,1) (2,2) wins on move 5
    assert lines.index("X WINS!") < lines.index("")


def t_game_arena():
    lines = run_program("game_lab.jr").splitlines()
    arena = lines[lines.index("") + 1:]
    assert arena == [
        "A hits B for 12 -> B: 38",
        "B hits A for 15 -> A: 35",
        "A hits B for 9 -> B: 29",
        "B hits A for 20 -> A: 15",
        "A hits B for 7 -> B: 22",
        "B hits A for 11 -> A: 4",
        "A hits B for 30 -> B: -8",
        "A WINS THE ARENA!",
    ]


# ------------------------------------------------------------------ the real CLI
def run_cli(name):
    proc = subprocess.run(
        [sys.executable, "juru.py", os.path.join("examples", "test", name)],
        capture_output=True, text=True, cwd=HERE,
    )
    return proc


def t_cli_number():
    proc = run_cli("number_lab.jr")
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    assert proc.stdout == NUMBER_LAB, "stdout mismatch:\n" + proc.stdout


def t_cli_algo():
    proc = run_cli("algo_lab.jr")
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    assert proc.stdout == ALGO_LAB, "stdout mismatch:\n" + proc.stdout


def t_cli_game():
    proc = run_cli("game_lab.jr")
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    assert proc.stdout == GAME_LAB, "stdout mismatch:\n" + proc.stdout


ALL = [
    ("number_lab passes the checker", t_number_checker),
    ("number_lab exact output", t_number_exact),
    ("number_lab key lines", t_number_lines),
    ("algo_lab passes the checker", t_algo_checker),
    ("algo_lab exact output", t_algo_exact),
    ("algo_lab key lines", t_algo_lines),
    ("game_lab passes the checker", t_game_checker),
    ("game_lab exact output", t_game_exact),
    ("game_lab wins on move 5", t_game_win),
    ("game_lab arena fight", t_game_arena),
    ("CLI: juru.py number_lab.jr", t_cli_number),
    ("CLI: juru.py algo_lab.jr", t_cli_algo),
    ("CLI: juru.py game_lab.jr", t_cli_game),
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
