"""JuRu Step 6 tests — dicts, for-in, in/not-in, slices, strings, math.

Every builtin here is guarded twice: the checker rejects wrong arity
BEFORE running, the interpreter rejects wrong value types WHILE running —
and both must print the same message (the mirror rule).
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
    tree = check_source(src) if with_checker else parse_source(src)
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


# ------------------------------------------------------------------ dicts
def t_dict_literal_display():
    assert run('say({"name": "Aman", "age": 20})') == "{name: Aman, age: 20}\n"


def t_dict_int_keys():
    assert run('d = {1: "one", 2: "two"}\nsay(d[2])\nsay(d)') == "two\n{1: one, 2: two}\n"


def t_dict_read_write():
    assert run(
        'd = {"a": 1}\n'
        'say(d["a"])\n'
        'd["a"] = 9\n'
        'd["b"] = 2\n'
        'say(d)\n'
    ) == "1\n{a: 9, b: 2}\n"


def t_dict_empty_display():
    assert run("d = {}\nsay(d)") == "{}\n"


def t_dict_missing_key():
    expect_galti('d = {}\nsay(d["x"])',
                 "key 'x' was not found — this dict is empty")
    expect_galti('d = {"a": 1, "b": 2}\nsay(d["z"])',
                 "key 'z' was not found — this dict has: a, b")
    expect_galti('d = {}\nfor i from 1 to 10 { d[i] = i }\nsay(d[99])',
                 "this dict has 10 keys")


def t_dict_dot_sugar():
    assert run('d = {"name": "JuRu"}\nsay(d.name)') == "JuRu\n"
    expect_galti('d = {"name": "JuRu"}\nsay(d.nope)',
                 "key 'nope' was not found — this dict has: name")


def t_dict_len_and_in():
    assert run('d = {"a": 1, "b": 2}\nsay(len(d))\nsay("a" in d)\nsay("z" in d)') == \
        "2\ntrue\nfalse\n"


def t_dict_key_guards():
    expect_galti('d = {}\nd[1.5] = 1', "a dict key must be text or a whole number — got: 1.5")
    expect_galti('d = {}\nd[true] = 1', "a dict key must be text or a whole number — got: true")
    expect_galti('d = {}\nd[[1]] = 1', "a dict key must be text or a whole number — got: [1]")
    expect_galti('d = {}\nd[null] = 1', "a dict key must be text or a whole number — got: null")
    expect_galti('say({"a": 1}[1.5])', "a dict key must be text or a whole number")


def t_dict_truthiness():
    assert run('if {} { say("full") } else { say("empty dict is false") }') == \
        "empty dict is false\n"
    assert run('if {"a": 1} { say("non-empty is true") }') == "non-empty is true\n"


def t_dict_equality():
    assert run('say({"a": 1} == {"a": 1})\nsay({"a": 1} == {"a": 2})\n'
               'say({"a": 1} != {"b": 1})') == "true\nfalse\ntrue\n"


def t_dict_nested_and_alias():
    assert run(
        'grid = {"row": {"x": 1}}\n'
        'say(grid["row"]["x"])\n'
        'say(grid.row.x)\n'
        'same = grid\n'
        'grid["row"]["x"] = 7\n'
        'say(same.row.x)\n'
    ) == "1\n1\n7\n"


def t_dict_of_dicts_display():
    assert run('say({"outer": {"in": 1}})') == "{outer: {in: 1}}\n"


def t_dict_word_count():
    assert run(
        'counts = {}\n'
        'for w in split("a b a c a", " ") {\n'
        '    if w in counts {\n'
        '        counts[w] = counts[w] + 1\n'
        '    } else {\n'
        '        counts[w] = 1\n'
        '    }\n'
        '}\n'
        'say(counts["a"])\n'
        'say(len(counts))\n'
    ) == "3\n3\n"


# ------------------------------------------------------------------ for-in
def t_for_in_list():
    assert run("for x in [10, 20, 30] {\n    say(x)\n}") == "10\n20\n30\n"


def t_for_in_text():
    assert run('for ch in "ab" {\n    say(ch)\n}') == "a\nb\n"


def t_for_in_dict_keys():
    assert run('for k in {"a": 1, "b": 2} {\n    say(k)\n}') == "a\nb\n"


def t_for_in_break_continue():
    assert run(
        "hits = 0\n"
        "for x in [1, 2, 3, 4, 5, 6] {\n"
        "    if x == 2 {\n"
        "        continue\n"
        "    }\n"
        "    if x == 5 {\n"
        "        break\n"
        "    }\n"
        "    hits = hits + 1\n"
        "}\n"
        "say(hits)\n"
    ) == "3\n"        # 1, 3, 4 — 2 skipped by continue, 5 stops the loop


def t_for_in_guarded_types():
    expect_galti("for x in 5 { say(x) }",
                 "'for x in ...' needs a list, text, dict, or set — got: 5")
    expect_galti("for x in null { say(x) }",
                 "'for x in ...' needs a list, text, dict, or set — got: null")
    expect_galti("for x in true { say(x) }",
                 "'for x in ...' needs a list, text, dict, or set — got: true")


def t_for_in_loop_var_survives():
    assert run("for x in [7, 8] { }\nsay(x)") == "8\n"


def t_for_in_push_inside_is_safe():
    """The loop walks a copy — pushing during the loop cannot run forever."""
    assert run(
        "data = [1, 2]\n"
        "for x in data {\n"
        "    push(data, x * 10)\n"
        "}\n"
        "say(len(data))\n"
        "say(data)\n"
    ) == "4\n[1, 2, 10, 20]\n"


def t_both_for_forms_together():
    assert run(
        "total = 0\n"
        "for i from 1 to 3 {\n"
        "    for x in [10, 20] {\n"
        "        total = total + x + i\n"
        "    }\n"
        "}\n"
        "say(total)\n"
    ) == "102\n"       # per i: (10+i) + (20+i) = 32 + 34 + 36


# ------------------------------------------------------------------ in / not in
def t_in_list_and_text_and_dict():
    assert run('say(2 in [1, 2, 3])\nsay(9 in [1, 2, 3])') == "true\nfalse\n"
    assert run('say("ell" in "hello")\nsay("z" in "hello")') == "true\nfalse\n"
    assert run('say("a" in {"a": 1})\nsay(1 in {"a": 1})') == "true\nfalse\n"


def t_not_in():
    assert run("say(4 not in [1, 2, 3])\nsay(2 not in [1, 2, 3])") == "true\nfalse\n"
    assert run('say("z" not in "hey")\nsay("q" not in {"a": 1})') == "true\ntrue\n"


def t_in_uses_equality_rules():
    """true != 1 inside lists too — the same clean categories."""
    assert run("say(true in [1])\nsay(1 in [true])\nsay(1 in [1.0])") == \
        "false\nfalse\ntrue\n"


def t_in_precedence():
    assert run("say(1 + 1 in [2])") == "true\n"


def t_in_type_guards():
    expect_galti("say(5 in 5)", "'in' needs a list, text, dict, or set on the right — got: 5")
    expect_galti("say(5 in null)", "'in' needs a list, text, dict, or set on the right — got: null")
    expect_galti('say(5 in "abc")', "'in' on text needs text on the left — got: 5")
    expect_galti('say(1.5 in {"a": 1})', "a dict key must be text or a whole number")


# ------------------------------------------------------------------ slices
def t_slice_text():
    assert run('say("hello world"[0:5])') == "hello\n"
    assert run('say("hello"[1:4])') == "ell\n"


def t_slice_list():
    assert run("say([10, 20, 30, 40][1:3])") == "[20, 30]\n"


def t_slice_open_ends():
    assert run('say("abcdef"[2:])') == "cdef\n"
    assert run('say("abcdef"[:3])') == "abc\n"
    assert run("say([1, 2, 3][:])") == "[1, 2, 3]\n"


def t_slice_clamps():
    """Out-of-range never crashes — a slice just gives what exists."""
    assert run("say([1, 2, 3][1:99])") == "[2, 3]\n"
    assert run('say("hi"[:99])') == "hi\n"
    assert run("say([1, 2, 3][2:1])") == "[]\n"
    assert run("say([1, 2, 3][9:9])") == "[]\n"


def t_slice_guards():
    # negative bounds now count backwards (Step 22) — they are a feature
    assert run("say([1][-1:2])") == "[1]\n"
    assert run("say([1][0:-1])") == "[]\n"
    expect_galti("say([1, 2, 3][::0])", "the slice step cannot be zero")
    expect_galti("say([1, 2, 3][::1.5])", "the slice step must be a whole number (int)")
    expect_galti('say("ab"["x":1])', "the slice start must be a whole number")
    expect_galti('say("ab"[0:"x"])', "the slice end must be a whole number")
    expect_galti("say([1][true:2])", "the slice start must be a whole number")
    expect_galti("say([1][0:1.5])", "the slice end must be a whole number")
    expect_galti('say({1: "x"}[1.5])', "a dict key must be text or a whole number")
    expect_galti("say(5[0:1])", "slices work on lists and text — got: 5")
    expect_galti('say({"a": 1}[0:1])', "slices work on lists and text — got: {a: 1}")


def t_plain_index_still_int_only():
    expect_galti("say([1, 2][1.0])", "the index must be a whole number")


# ------------------------------------------------------------------ strings
def t_split():
    assert run('say(split("a,b,c", ","))') == "[a, b, c]\n"
    assert run('say(split("one", ","))') == "[one]\n"
    assert run('say(split("aXXb", "XX"))') == "[a, b]\n"


def t_split_guards():
    expect_galti('split("a", "")', "the split separator cannot be empty")
    expect_galti('split(5, ",")', "split() needs text — got: 5")
    expect_galti('split("a", 5)', "the split separator must be text — got: 5")


def t_join():
    assert run('say(join(["x", "y"], "-"))') == "x-y\n"
    assert run('say(join([1, 2], "+"))') == "1+2\n"
    assert run('say(join([], "-"))') == "\n"


def t_join_guards():
    expect_galti('join(5, "-")', "join() needs a list — got: 5")
    expect_galti('join(["a"], 5)', "the join separator must be text — got: 5")


def t_trim():
    assert run('say("[" + trim("  hi  ") + "]")') == "[hi]\n"
    assert run('say("[" + trim("\\t\\t a \\n") + "]")') == "[a]\n"
    expect_galti("trim(5)", "trim() needs text — got: 5")


def t_replace():
    assert run('say(replace("aaa", "a", "b"))') == "bbb\n"
    assert run('say(replace("one two", " ", "_"))') == "one_two\n"
    expect_galti('replace("a", "", "b")', "the old text cannot be empty in replace()")
    expect_galti('replace(5, "a", "b")', "replace() needs text — got: 5")


# ------------------------------------------------------------------ math
def t_abs():
    assert run("say(abs(-5))\nsay(abs(2.5))\nsay(abs(0))") == "5\n2.5\n0\n"
    expect_galti("abs(true)", "abs() needs a number — got: true")
    expect_galti('abs("x")', "abs() needs a number — got: x")


def t_round():
    assert run("say(round(2.5))\nsay(round(3.5))\nsay(round(2.4))\n"
               "say(round(2.6))\nsay(round(-2.5))\nsay(round(3))") == \
        "3\n4\n2\n3\n-3\n3\n"
    expect_galti('round("x")', "round() needs a number — got: x")


def t_sqrt():
    assert run("say(sqrt(9))") == "3.0\n"
    assert run("say(sqrt(2))") == "1.4142135623730951\n"
    assert run("say(sqrt(0))") == "0.0\n"
    expect_galti("sqrt(-1)", "sqrt(-1) — a negative number has no square root")
    expect_galti("sqrt(true)", "sqrt() needs a number — got: true")


def t_random_in_range():
    import random as pyrandom
    pyrandom.seed(7)      # deterministic dice for the test run
    out = run(
        "rolls = 0\n"
        "for i from 1 to 50 {\n"
        "    n = random(1, 6)\n"
        "    if n >= 1 and n <= 6 {\n"
        "        rolls = rolls + 1\n"
        "    }\n"
        "}\n"
        "say(rolls)\n"
    )
    assert out == "50\n", out
    expect_galti("random(6, 1)", "in random(low, high), low cannot be bigger than high (6 > 1)")
    expect_galti("random(1.5, 6)", "random() needs whole numbers — got: 1.5")


# ------------------------------------------------------------------ arity mirror
def t_checker_arity_step6():
    expect_check_galti("split(1)", "split(text, separator) takes exactly 2 arguments")
    expect_check_galti("join(1)", "join(list, separator) takes exactly 2 arguments")
    expect_check_galti("trim(1, 2)", "trim(x) takes exactly 1 argument")
    expect_check_galti("replace(1, 2)", "replace(text, old, new) takes exactly 3 arguments")
    expect_check_galti("abs(1, 2)", "abs(x) takes exactly 1 argument")
    expect_check_galti("round()", "round(x) takes exactly 1 argument")
    expect_check_galti("random(1)", "random(low, high) takes exactly 2 arguments")
    expect_check_galti("sqrt(1, 2)", "sqrt(x) takes exactly 1 argument")


def t_mirror_rule_step6():
    pairs = [
        ("split(1, 2, 3)", "split(text, separator) takes exactly 2 arguments"),
        ("join(1)", "join(list, separator) takes exactly 2 arguments"),
        ("replace(1, 2)", "replace(text, old, new) takes exactly 3 arguments"),
        ("abs()", "abs(x) takes exactly 1 argument"),
        ("round(1, 2)", "round(x) takes exactly 1 argument"),
        ("random(1)", "random(low, high) takes exactly 2 arguments"),
        ("sqrt()", "sqrt(x) takes exactly 1 argument"),
    ]
    for src, fragment in pairs:
        expect_mirrored(src, fragment)


def t_reserved_step6_builtins():
    expect_check_galti("split = 5", "'split' is reserved (builtin) — pick another name")
    expect_check_galti("trim = 5", "'trim' is reserved (builtin) — pick another name")
    expect_check_galti("abs = 5", "'abs' is reserved (builtin) — pick another name")
    expect_check_galti("random = 5", "'random' is reserved (builtin) — pick another name")
    expect_check_galti(
        "func join(a, b) {\n    return a\n}",
        "'join' is reserved (builtin) — pick another name")


# ------------------------------------------------------------------ demos
def t_dicts_demo_exact():
    path = os.path.join(HERE, "examples", "test", "dicts_demo.jr")
    with open(path, encoding="utf-8") as f:
        assert run(f.read()) == (
            "the -> 4\n"
            "cat -> 2\n"
            "saw -> 2\n"
            "dog -> 2\n"
            "and -> 1\n"
            "different words: 5\n"
        )


ALL = [
    ("dict literal + display", t_dict_literal_display),
    ("dict int keys", t_dict_int_keys),
    ("dict read/write", t_dict_read_write),
    ("empty dict display", t_dict_empty_display),
    ("dict missing key errors", t_dict_missing_key),
    ("dict dot sugar", t_dict_dot_sugar),
    ("dict len + in", t_dict_len_and_in),
    ("dict key guards", t_dict_key_guards),
    ("dict truthiness", t_dict_truthiness),
    ("dict equality", t_dict_equality),
    ("dict nested + alias", t_dict_nested_and_alias),
    ("dict inside dict display", t_dict_of_dicts_display),
    ("dict word counting", t_dict_word_count),
    ("for-in over a list", t_for_in_list),
    ("for-in over text", t_for_in_text),
    ("for-in over dict keys", t_for_in_dict_keys),
    ("for-in break/continue", t_for_in_break_continue),
    ("for-in type guards", t_for_in_guarded_types),
    ("for-in loop var survives", t_for_in_loop_var_survives),
    ("for-in push inside is safe", t_for_in_push_inside_is_safe),
    ("both for forms together", t_both_for_forms_together),
    ("in: list, text, dict", t_in_list_and_text_and_dict),
    ("not in", t_not_in),
    ("in uses equality rules", t_in_uses_equality_rules),
    ("in precedence with +", t_in_precedence),
    ("in type guards", t_in_type_guards),
    ("slices of text", t_slice_text),
    ("slices of lists", t_slice_list),
    ("open-ended slices", t_slice_open_ends),
    ("slices clamp, never crash", t_slice_clamps),
    ("slice guards", t_slice_guards),
    ("plain index still int-only", t_plain_index_still_int_only),
    ("split", t_split),
    ("split guards", t_split_guards),
    ("join", t_join),
    ("join guards", t_join_guards),
    ("trim", t_trim),
    ("replace", t_replace),
    ("abs", t_abs),
    ("round (no surprises)", t_round),
    ("sqrt", t_sqrt),
    ("random stays in range", t_random_in_range),
    ("checker arity (step 6)", t_checker_arity_step6),
    ("mirror rule (step 6)", t_mirror_rule_step6),
    ("reserved step 6 builtins", t_reserved_step6_builtins),
    ("dicts_demo exact output", t_dicts_demo_exact),
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
