"""JuRu Step 12 tests — stdlib wave 3: float, pow, pop, type.

The four tools users asked for when reading input and doing math:
  float(x)   text/int → decimal (the missing half of int())
  pow(a, b)  exponents, guarded (no ** operator to memorize)
  pop(list)  remove + return the last item (the counterpart of push)
  type(x)    the one-word answer: int, float, text, bool, null, list, dict, func, module

Zero new keywords. Every guard mirrors its checker message.
"""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
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


def run(src):
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=HERE)
    return buf.getvalue()


def expect_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wanted {!r}, got {!r}".format(
            fragment, err.message)
        return
    try:
        tree = check_source(src)
    except JuRuGalti:
        return
    try:
        Interpreter().run(tree, base_dir=HERE)
    except JuRuGalti as err:
        assert fragment in err.message, "wanted {!r}, got {!r}".format(
            fragment, err.message)
        return
    raise AssertionError("expected a JuRu error containing {!r}".format(fragment))


# ------------------------------------------------------------------ float
def t_float_from_int_and_text():
    assert run("say(float(5))") == "5.0\n"
    assert run("say(float(\"3.5\"))") == "3.5\n"
    assert run("say(float(\"-2\"))") == "-2.0\n"
    assert run("say(float(0))") == "0.0\n"


def t_float_round_trip_with_int():
    assert run("say(int(float(\"3.9\")))") == "3\n"
    assert run("say(float(int(\"7\")))") == "7.0\n"


def t_float_rejects_garbage():
    expect_galti("say(float(\"abc\"))", "float('abc') — 'abc' is not a number")
    expect_galti("say(float(true))", "float(true) — this cannot be converted to float")
    expect_galti("say(float(null))", "float(null) — this cannot be converted to float")
    expect_galti("say(float([1]))", "this cannot be converted to float")
    expect_galti("say(float({}))", "this cannot be converted to float")


def t_float_arity():
    expect_galti("say(float())", "float(x) takes exactly 1 argument")
    expect_galti("say(float(1, 2))", "float(x) takes exactly 1 argument")
    assert BUILTIN_ARITY["float"] == (1, 1)
    assert BUILTIN_HINT["float"] == "float(x) takes exactly 1 argument"


# ------------------------------------------------------------------ pow
def t_pow_happy_paths():
    assert run("say(pow(2, 10))") == "1024\n"
    assert run("say(pow(2, 0))") == "1\n"
    assert run("say(pow(2, -2))") == "0.25\n"
    assert run("say(pow(9, 0.5))") == "3.0\n"
    assert run("say(pow(-2, 3))") == "-8\n"
    assert run("say(pow(0, 5))") == "0\n"
    assert run("say(pow(2, 53))") == "9007199254740992\n"


def t_pow_rejects_non_numbers():
    expect_galti("say(pow(\"2\", 3))", "pow() needs numbers — got: text and int")
    expect_galti("say(pow(2, \"3\"))", "pow() needs numbers — got: int and text")
    expect_galti("say(pow(true, 2))", "pow() needs numbers")


def t_pow_impossible_cases_are_friendly():
    expect_galti("say(pow(0, -1))",
                 "in pow(a, b), 0 cannot be raised to a negative power")
    expect_galti("say(pow(-2, 0.5))",
                 "a negative base needs a whole-number exponent (got: 0.5)")
    expect_galti("say(pow(-8, 1.5))",
                 "a negative base needs a whole-number exponent (got: 1.5)")


def t_pow_never_explodes():
    """Huge results are refused in words, never a hang or a crash."""
    expect_galti("say(pow(2, 99999))", "the result is too big to show")
    expect_galti("say(pow(10.0, 400))", "the result is too big to show")
    # modest results still work even near the caps
    assert run("say(pow(2, 64))") == "18446744073709551616\n"


def t_pow_arity():
    expect_galti("say(pow(2))", "pow(a, b) takes exactly 2 arguments")
    expect_galti("say(pow(1, 2, 3))", "pow(a, b) takes exactly 2 arguments")
    assert BUILTIN_ARITY["pow"] == (2, 2)


# ------------------------------------------------------------------ pop
def t_pop_returns_and_mutates():
    assert run("nums = [1, 2, 3]\nsay(pop(nums))\nsay(nums)") == "3\n[1, 2]\n"
    assert run("items = [\"a\"]\nsay(pop(items))\nsay(items)") == "a\n[]\n"


def t_pop_pairs_with_push():
    src = ("stack = []\n"
           "push(stack, 1)\n"
           "push(stack, 2)\n"
           "say(pop(stack))\n"
           "say(pop(stack))\n"
           "say(len(stack))\n")
    assert run(src) == "2\n1\n0\n"


def t_pop_empty_and_non_list():
    expect_galti("say(pop([]))", "pop() — this list is empty, there is nothing to take")
    expect_galti("say(pop(5))", "pop() needs a list — got: 5")
    expect_galti("say(pop(\"ab\"))", "pop() needs a list — got: ab")
    expect_galti("say(pop({}))", "pop() needs a list — got: {}")


def t_pop_arity():
    expect_galti("say(pop())", "pop(list) takes exactly 1 argument")
    expect_galti("say(pop([1], [2]))", "pop(list) takes exactly 1 argument")
    assert BUILTIN_ARITY["pop"] == (1, 1)


# ------------------------------------------------------------------ type
def t_type_names_all_values():
    assert run("say(type(5))") == "int\n"
    assert run("say(type(5.0))") == "float\n"
    assert run("say(type(\"hi\"))") == "text\n"
    assert run("say(type(true))") == "bool\n"
    assert run("say(type(false))") == "bool\n"
    assert run("say(type(null))") == "null\n"
    assert run("say(type([1]))") == "list\n"
    assert run("say(type({}))") == "dict\n"


def t_type_funcs_and_modules():
    assert run("func f() {\n    return 1\n}\nsay(type(f))") == "func\n"
    src = "import \"examples/helpers.jr\"\nsay(type(helpers))"
    assert run(src) == "module\n"


def t_type_never_fails_and_validates_input():
    """The real use: check what ask() gave you before converting."""
    src = ("value = \"3.5\"\n"
           "if type(value) == \"text\" {\n"
           "    say(\"it is text\")\n"
           "}\n"
           "if type(4) == \"int\" {\n"
           "    say(\"it is int\")\n"
           "}\n")
    assert run(src) == "it is text\nit is int\n"


def t_type_arity():
    expect_galti("say(type())", "type(x) takes exactly 1 argument")
    expect_galti("say(type(1, 2))", "type(x) takes exactly 1 argument")
    assert BUILTIN_ARITY["type"] == (1, 1)


# ------------------------------------------------------------------ integration + purity
def t_input_pipeline_int_and_float():
    """The end-to-end reason wave 3 exists: read text, convert safely."""
    src = ("raw = \"3.5\"\n"
           "if type(raw) == \"text\" {\n"
           "    if trim(raw) == \"\" {\n"
           "        say(\"empty\")\n"
           "    } else {\n"
           "        say(float(raw) + 1)\n"
           "    }\n"
           "}\n")
    assert run(src) == "4.5\n"


def t_checker_and_interpreter_agree():
    """Every builtin in the checker has an arity and a hint (and vice versa)."""
    assert len(BUILTINS) == 28
    assert set(BUILTIN_ARITY) == set(BUILTINS)
    assert set(BUILTIN_HINT) == set(BUILTINS)


def t_all_reserved_again():
    for name in ("float", "pow", "pop", "type"):
        try:
            check_source("{} = 1".format(name))
        except JuRuGalti as err:
            assert "'{}' is reserved (builtin)".format(name) in err.message, err.message
        else:
            raise AssertionError(name + " was shadowable")


def t_no_new_keywords():
    assert len(KEYWORDS) == 19


def t_purity_pop_mutates_only_in_place():
    """push and pop are the only builtins that change a list in place;
    float/pow/type never mutate anything."""
    src = ("nums = [3, 1]\n"
           "say(type(nums))\n"
           "say(pow(len(nums), 2))\n"
           "say(float(2))\n"
           "say(nums)\n")
    assert run(src) == "list\n4\n2.0\n[3, 1]\n"


ALL = [
    ("float: int and text become decimal", t_float_from_int_and_text),
    ("float: round-trips with int", t_float_round_trip_with_int),
    ("float: garbage refused in words", t_float_rejects_garbage),
    ("float: arity + mirror messages", t_float_arity),
    ("pow: happy paths", t_pow_happy_paths),
    ("pow: non-numbers refused", t_pow_rejects_non_numbers),
    ("pow: impossible math explained", t_pow_impossible_cases_are_friendly),
    ("pow: never explodes", t_pow_never_explodes),
    ("pow: arity + mirror messages", t_pow_arity),
    ("pop: returns last, mutates in place", t_pop_returns_and_mutates),
    ("pop: pairs with push (a stack)", t_pop_pairs_with_push),
    ("pop: empty + non-list refused", t_pop_empty_and_non_list),
    ("pop: arity + mirror messages", t_pop_arity),
    ("type: names every value", t_type_names_all_values),
    ("type: funcs and modules too", t_type_funcs_and_modules),
    ("type: input validation pattern", t_type_never_fails_and_validates_input),
    ("type: arity + mirror messages", t_type_arity),
    ("the ask() pipeline: text → float", t_input_pipeline_int_and_float),
    ("checker ↔ interpreter tables agree", t_checker_and_interpreter_agree),
    ("new names are reserved", t_all_reserved_again),
    ("zero new keywords", t_no_new_keywords),
    ("purity: only push/pop mutate", t_purity_pop_mutates_only_in_place),
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
