"""JuRu Step 9 tests — the second stdlib wave (still 0 new keywords).

sorted / reverse / find / keys / values / count — every one guarded twice:
the checker rejects wrong arity BEFORE running, the interpreter rejects wrong
value types WHILE running, and both print the same message (mirror rule).

Note on the easy story: sorted and reverse give you a NEW list — only push
changes a list in place. find misses with -1, never a crash.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import JuRuGalti, KEYWORDS
from parser import parse_source
from checker import check_source
from interpreter import Interpreter

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


def run(src):
    tree = check_source(src)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree)
    return buf.getvalue()


def expect_galti(src, fragment):
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


def expect_mirrored(src, fragment):
    """Checker AND runtime must reject with the same message."""
    expect_check_galti(src, fragment)
    expect_galti(src, fragment)


# ------------------------------------------------------------------ sorted
def t_sorted_numbers():
    assert run("say(sorted([3, 1, 4.5, 2]))") == "[1, 2, 3, 4.5]\n"
    assert run("say(sorted([]))") == "[]\n"
    assert run("say(sorted([5]))") == "[5]\n"


def t_sorted_text():
    assert run('say(sorted(["z", "a", "m"]))') == "[a, m, z]\n"
    assert run('say(sorted(["banana", "apple"]))') == "[apple, banana]\n"


def t_sorted_is_pure():
    """The original list stays untouched — only push changes a list."""
    assert run(
        "nums = [3, 1, 2]\n"
        "up = sorted(nums)\n"
        "say(nums)\n"
        "say(up)\n"
    ) == "[3, 1, 2]\n[1, 2, 3]\n"


def t_sorted_guards():
    expect_galti("sorted(5)", "sorted() needs a list — got: 5")
    expect_galti('sorted("abc")', "sorted() needs a list — got: abc")
    expect_galti('sorted([1, "a"])',
                 "sorted() needs a list of only numbers or only text — got: [1, a]")
    expect_galti("sorted([true, false])",
                 "sorted() needs a list of only numbers or only text — got: [true, false]")
    expect_galti("sorted([null])",
                 "sorted() needs a list of only numbers or only text — got: [null]")


# ------------------------------------------------------------------ reverse
def t_reverse_numbers_and_text_items():
    assert run("say(reverse([1, 2, 3]))") == "[3, 2, 1]\n"
    assert run('say(reverse(["a", "b"]))') == "[b, a]\n"
    assert run("say(reverse([]))") == "[]\n"


def t_reverse_is_pure():
    assert run(
        "nums = [1, 2]\n"
        "back = reverse(nums)\n"
        "say(nums)\n"
        "say(back)\n"
    ) == "[1, 2]\n[2, 1]\n"


def t_reverse_guards():
    expect_galti('reverse("ab")', "reverse() needs a list — got: ab")
    expect_galti("reverse(5)", "reverse() needs a list — got: 5")
    expect_galti("reverse({})", "reverse() needs a list — got: {}")


# ------------------------------------------------------------------ find
def t_find_basic():
    assert run("say(find([5, 7, 9], 9))") == "2\n"
    assert run('say(find(["a", "b", "c"], "b"))') == "1\n"
    assert run("say(find([1, 2], 99))") == "-1\n"
    assert run("say(find([], 1))") == "-1\n"


def t_find_first_match_and_equality():
    assert run("say(find([1, 2, 1], 1))") == "0\n"
    assert run("say(find([1.0, 2], 1))") == "0\n"     # 1 finds 1.0 (same family)
    assert run("say(find([true], 1))") == "-1\n"      # bools are a different world
    assert run("say(find([[1, 2]], [1, 2]))") == "0\n"  # deep equality


def t_find_guards():
    expect_galti("find(5, 1)", "find() needs a list first — got: 5")
    expect_galti('find("abc", "b")', "find() needs a list first — got: abc")


# ------------------------------------------------------------------ keys / values
def t_keys_values():
    assert run('say(keys({"a": 1, "b": 2}))') == "[a, b]\n"
    assert run('say(values({"a": 1, "b": 2}))') == "[1, 2]\n"
    assert run("say(keys({}))") == "[]\n"
    assert run("say(values({}))") == "[]\n"
    assert run('say(keys({10: "x", 2: "y"}))') == "[10, 2]\n"


def t_keys_values_keep_order():
    assert run(
        'd = {}\n'
        'd["z"] = 1\n'
        'd["a"] = 2\n'
        'd["m"] = 3\n'
        'say(keys(d))\n'
        'say(values(d))\n'
    ) == "[z, a, m]\n[1, 2, 3]\n"


def t_keys_values_guards():
    expect_galti("keys([1])", "keys() needs a dict — got: [1]")
    expect_galti("values(5)", "values() needs a dict — got: 5")
    expect_galti('keys("ab")', "keys() needs a dict — got: ab")


# ------------------------------------------------------------------ count
def t_count_basic():
    assert run('say(count(["x", "y", "x"], "x"))') == "2\n"
    assert run("say(count([1, 1, 1], 1))") == "3\n"
    assert run("say(count([], 1))") == "0\n"
    assert run('say(count(["a"], "b"))') == "0\n"


def t_count_equality_rules():
    assert run("say(count([1, 1.0, true], 1))") == "2\n"   # 1 finds 1.0, not true
    assert run("say(count([[1], [1]], [1]))") == "2\n"     # deep equality


def t_count_guards():
    expect_galti("count(5, 1)", "count() needs a list first — got: 5")
    expect_galti('count("ab", "a")', "count() needs a list first — got: ab")


# ------------------------------------------------------------------ combos
def t_step9_pipeline():
    """The tools working together — a tiny top-3 word counter."""
    assert run(
        'words = split("go go stop go wait stop", " ")\n'
        'best = 0\n'
        'word = ""\n'
        'for w in keys({"go": 0, "stop": 0, "wait": 0}) {\n'
        '    n = count(words, w)\n'
        '    if n > best {\n'
        '        best = n\n'
        '        word = w\n'
        '    }\n'
        '}\n'
        'say(word + " x" + best)\n'
        'say(sorted(words))\n'
        'say(find(words, "wait"))\n'
    ) == "go x3\n[go, go, go, stop, stop, wait]\n4\n"


def t_reverse_of_sorted():
    assert run("say(reverse(sorted([3, 1, 2])))") == "[3, 2, 1]\n"
    assert run("say(sorted(reverse([3, 1, 2])))") == "[1, 2, 3]\n"


def t_in_list_context():
    assert run(
        "data = [4, 2, 9]\n"
        "if 9 in sorted(data) and find(data, 9) == 2 {\n"
        "    say(\"all tools agree\")\n"
        "}\n"
    ) == "all tools agree\n"


# ------------------------------------------------------------------ arity mirror
def t_checker_arity_step9():
    expect_check_galti("sorted(1, 2)", "sorted(list) takes exactly 1 argument")
    expect_check_galti("reverse(1, 2)", "reverse(list) takes exactly 1 argument")
    expect_check_galti("find(1)", "find(list, item) takes exactly 2 arguments")
    expect_check_galti("keys()", "keys(dict) takes exactly 1 argument")
    expect_check_galti("values(1, 2)", "values(dict) takes exactly 1 argument")
    expect_check_galti("count(1)", "count(list, item) takes exactly 2 arguments")


def t_mirror_rule_step9():
    pairs = [
        ("sorted(1, 2)", "sorted(list) takes exactly 1 argument"),
        ("reverse()", "reverse(list) takes exactly 1 argument"),
        ("find(1)", "find(list, item) takes exactly 2 arguments"),
        ("keys(1, 2)", "keys(dict) takes exactly 1 argument"),
        ("values()", "values(dict) takes exactly 1 argument"),
        ("count(1)", "count(list, item) takes exactly 2 arguments"),
    ]
    for src, fragment in pairs:
        expect_mirrored(src, fragment)


def t_reserved_step9_builtins():
    expect_check_galti("sorted = 5", "'sorted' is reserved (builtin) — pick another name")
    expect_check_galti("reverse = 5", "'reverse' is reserved (builtin) — pick another name")
    expect_check_galti("find = 5", "'find' is reserved (builtin) — pick another name")
    expect_check_galti("keys = 5", "'keys' is reserved (builtin) — pick another name")
    expect_check_galti("values = 5", "'values' is reserved (builtin) — pick another name")
    expect_check_galti("count = 5", "'count' is reserved (builtin) — pick another name")
    expect_check_galti(
        "func sorted(a) {\n    return a\n}",
        "'sorted' is reserved (builtin) — pick another name")


def t_no_new_keywords():
    """Step 9 added tools, not keywords — the language stays small."""
    assert len(KEYWORDS) == 19
    assert "sorted" not in KEYWORDS


ALL = [
    ("sorted: numbers", t_sorted_numbers),
    ("sorted: text", t_sorted_text),
    ("sorted: never mutates", t_sorted_is_pure),
    ("sorted guards", t_sorted_guards),
    ("reverse", t_reverse_numbers_and_text_items),
    ("reverse: never mutates", t_reverse_is_pure),
    ("reverse guards", t_reverse_guards),
    ("find: found / -1", t_find_basic),
    ("find: first match + equality", t_find_first_match_and_equality),
    ("find guards", t_find_guards),
    ("keys + values", t_keys_values),
    ("keys + values keep order", t_keys_values_keep_order),
    ("keys/values guards", t_keys_values_guards),
    ("count", t_count_basic),
    ("count equality rules", t_count_equality_rules),
    ("count guards", t_count_guards),
    ("tools together (top word)", t_step9_pipeline),
    ("reverse of sorted", t_reverse_of_sorted),
    ("all tools agree", t_in_list_context),
    ("checker arity (step 9)", t_checker_arity_step9),
    ("mirror rule (step 9)", t_mirror_rule_step9),
    ("reserved step 9 builtins", t_reserved_step9_builtins),
    ("no new keywords", t_no_new_keywords),
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
