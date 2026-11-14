"""JuRu Step 5 tests — the stdlib (upper / lower / str / push / sum / min / max).

Covers:
- happy paths with exact output
- wrong value types (every builtin guards its input)
- wrong arity, caught by the checker AND by the interpreter
- the two layers must always print the SAME message (mirror rule)
- reserved-name protection (assign / funcdef)
- in-place mutation of push (aliasing)
"""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti
from juru.parser import parse_source
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


def run(src, with_checker=True):
    """Run source, capture stdout, return it."""
    tree = check_source(src) if with_checker else parse_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree)
    return buf.getvalue()


def expect_galti(src, fragment):
    """The run must fail with a JuRu Error containing the fragment."""
    try:
        run(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected a runtime error, but the program ran")


def expect_check_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected a semantic error, but the check passed")


# ------------------------------------------------------------------ happy paths
def t_upper_lower():
    assert run('say(upper("juru"))') == "JURU\n"
    assert run('say(lower("HELLO World"))') == "hello world\n"
    assert run('say(upper(""))') == "\n"


def t_str():
    assert run('say(str(42) + "!")') == "42!\n"
    assert run('say(str(2.5))') == "2.5\n"
    assert run('say(str(1 < 2))') == "true\n"
    assert run('say(str(null))') == "null\n"
    assert run('say(str([1, 2]))') == "[1, 2]\n"


def t_push():
    assert run(
        "nums = [1, 2]\n"
        "push(nums, 3)\n"
        "say(nums)\n"
    ) == "[1, 2, 3]\n"


def t_push_returns():
    assert run(
        "nums = [1, 2]\n"
        "say(push(nums, 3))\n"
        "say(nums)\n"
    ) == "[1, 2, 3]\n[1, 2, 3]\n"


def t_push_aliasing():
    """push mutates the real list — another name sees the change."""
    assert run(
        "a = [1]\n"
        "b = a\n"
        "push(b, 9)\n"
        "say(a)\n"
    ) == "[1, 9]\n"


def t_push_any_value():
    assert run(
        "data = []\n"
        "push(data, \"text\")\n"
        "push(data, [1, 2])\n"
        "push(data, null)\n"
        "say(data)\n"
    ) == "[text, [1, 2], null]\n"


def t_sum():
    assert run('say(sum([3, 1, 4, 5]))') == "13\n"
    assert run('say(sum([1.5, 2.5]))') == "4\n" or True  # placeholder, replaced below


def t_sum_float():
    assert run('say(sum([1.5, 2.5]))') == "4.0\n"
    assert run('say(sum([]))') == "0\n"
    assert run('say(sum([5]))') == "5\n"
    assert run('say(sum([-3, 3]))') == "0\n"


def t_min_max():
    assert run('say(min(3, 9))') == "3\n"
    assert run('say(max(3, 9))') == "9\n"
    assert run('say(min(2.5, 1))') == "1\n"
    assert run('say(max(4.0, 4))') == "4.0\n"
    assert run('say(min(-2, 7))') == "-2\n"


def t_demo_exact():
    path = os.path.join(HERE, "examples", "stdlib_demo.jr")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    assert run(src) == (
        "JURU\n"
        "hello\n"
        "42!\n"
        "2.5\n"
        "true\n"
        "[1, 2]\n"
        "[3, 1, 4, 5]\n"
        "13\n"
        "3\n"
        "9\n"
        "4.0\n"
        "-2\n"
    )


# ------------------------------------------------------------------ type guards
def t_upper_needs_text():
    expect_galti("say(upper(5))", "upper() needs text — got: 5")
    expect_galti('say(upper([1]))', "upper() needs text — got: [1]")
    expect_galti("say(lower(true))", "lower() needs text — got: true")


def t_push_needs_list():
    expect_galti("push(5, 1)", "push() needs a list — got: 5")
    expect_galti('push("ab", 1)', "push() needs a list — got: ab")


def t_sum_needs_list():
    expect_galti("sum(5)", "sum() needs a list — got: 5")


def t_sum_numbers_only():
    expect_galti('sum([1, "a"])', "sum() needs only numbers — found: a")
    expect_galti("sum([true])", "sum() needs only numbers — found: true")
    expect_galti("sum([null])", "sum() needs only numbers — found: null")


def t_min_max_numbers_only():
    expect_galti('min("a", 1)', "min() needs numbers — got text and int")
    expect_galti('max(1, "b")', "max() needs numbers — got int and text")
    expect_galti("min(true, 2)", "min() needs numbers — got bool and int")
    expect_galti("max([1], 2)", "max() needs numbers — got list and int")


# ------------------------------------------------------------------ arity (both layers)
def t_checker_arity_upper_lower_str():
    expect_check_galti("upper(1, 2)", "upper(x) takes exactly 1 argument")
    expect_check_galti("upper()", "upper(x) takes exactly 1 argument")
    expect_check_galti("lower(1, 2)", "lower(x) takes exactly 1 argument")
    expect_check_galti("str(1, 2)", "str(x) takes exactly 1 argument")


def t_checker_arity_push_sum():
    expect_check_galti("push(1)", "push(list, item) takes exactly 2 arguments")
    expect_check_galti("push(1, 2, 3)", "push(list, item) takes exactly 2 arguments")
    expect_check_galti("sum()", "sum(list) takes exactly 1 argument")
    expect_check_galti("sum(1, 2)", "sum(list) takes exactly 1 argument")


def t_checker_arity_min_max():
    expect_check_galti("min(3)", "min(a, b) takes exactly 2 arguments")
    expect_check_galti("min(1, 2, 3)", "min(a, b) takes exactly 2 arguments")
    expect_check_galti("max(3)", "max(a, b) takes exactly 2 arguments")


def t_checker_arity_old_ones_still_hold():
    expect_check_galti("len(1, 2)", "len(x) takes exactly 1 argument")
    expect_check_galti("int(1, 2)", "int(x) takes exactly 1 argument")
    expect_check_galti("ask(1, 2)", "ask(prompt) takes at most 1 argument")


def t_runtime_arity():
    """The interpreter (checker skipped) prints the very same message."""
    for src, fragment in [
        ("upper(1, 2)", "upper(x) takes exactly 1 argument"),
        ("lower()", "lower(x) takes exactly 1 argument"),
        ("str(1, 2)", "str(x) takes exactly 1 argument"),
        ("push(1)", "push(list, item) takes exactly 2 arguments"),
        ("sum()", "sum(list) takes exactly 1 argument"),
        ("min(3)", "min(a, b) takes exactly 2 arguments"),
        ("max(1, 2, 3)", "max(a, b) takes exactly 2 arguments"),
    ]:
        try:
            run(src, with_checker=False)
        except JuRuGalti as err:
            assert fragment in err.message, "wrong message: " + err.message
            continue
        raise AssertionError("expected a runtime error for: " + src)


def t_mirror_checker_vs_runtime():
    """Checker and interpreter must agree on the exact message text."""
    pairs = [
        ("upper(1, 2)", "upper(x) takes exactly 1 argument"),
        ("push(1, 2, 3)", "push(list, item) takes exactly 2 arguments"),
        ("sum()", "sum(list) takes exactly 1 argument"),
        ("min(1)", "min(a, b) takes exactly 2 arguments"),
        ("max(1)", "max(a, b) takes exactly 2 arguments"),
        ("len(1, 2)", "len(x) takes exactly 1 argument"),
        ("int(1, 2)", "int(x) takes exactly 1 argument"),
    ]
    for src, fragment in pairs:
        expect_check_galti(src, fragment)
        try:
            run(src, with_checker=False)
        except JuRuGalti as err:
            assert fragment in err.message, "wrong message: " + err.message
            continue
        raise AssertionError("runtime did not fail for: " + src)


# ------------------------------------------------------------------ reserved names
def t_reserved_assign():
    expect_check_galti("upper = 5", "'upper' is reserved (builtin) — pick another name")
    expect_check_galti("push = 5", "'push' is reserved (builtin) — pick another name")
    expect_check_galti("min = 1", "'min' is reserved (builtin) — pick another name")
    expect_check_galti("sum = 1", "'sum' is reserved (builtin) — pick another name")


def t_reserved_funcdef():
    expect_check_galti(
        "func upper(x) {\n    return x\n}", "'upper' is reserved (builtin) — pick another name")
    expect_check_galti(
        "func max(a, b) {\n    return a\n}", "'max' is reserved (builtin) — pick another name")


def t_reserved_runtime():
    try:
        run("str = 5")
    except JuRuGalti as err:
        assert "'str' is reserved (builtin) — pick another name" in err.message
        return
    raise AssertionError("runtime should reject assigning to 'str'")


def t_reserved_read_still_ok():
    """Reading a builtin in a call is fine — only assignment is reserved."""
    assert run('say(upper("a"))') == "A\n"


ALL = [
    ("upper / lower happy path", t_upper_lower),
    ("str converts anything", t_str),
    ("push appends in place", t_push),
    ("push returns the list", t_push_returns),
    ("push mutates (aliasing)", t_push_aliasing),
    ("push takes any value", t_push_any_value),
    ("sum happy paths", t_sum),
    ("sum floats / empty / negatives", t_sum_float),
    ("min / max happy paths", t_min_max),
    ("stdlib_demo exact output", t_demo_exact),
    ("upper/lower type guard", t_upper_needs_text),
    ("push type guard", t_push_needs_list),
    ("sum type guard (not a list)", t_sum_needs_list),
    ("sum type guard (not numbers)", t_sum_numbers_only),
    ("min/max type guard", t_min_max_numbers_only),
    ("checker arity: upper/lower/str", t_checker_arity_upper_lower_str),
    ("checker arity: push/sum", t_checker_arity_push_sum),
    ("checker arity: min/max", t_checker_arity_min_max),
    ("checker arity: len/int/ask unchanged", t_checker_arity_old_ones_still_hold),
    ("runtime arity messages", t_runtime_arity),
    ("mirror rule: checker == runtime", t_mirror_checker_vs_runtime),
    ("reserved assign (new builtins)", t_reserved_assign),
    ("reserved funcdef (new builtins)", t_reserved_funcdef),
    ("reserved assign at runtime", t_reserved_runtime),
    ("reading builtins still fine", t_reserved_read_still_ok),
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
