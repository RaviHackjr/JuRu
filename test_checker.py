"""JuRu Step 3 tests — Semantic Checker (catches mistakes before running)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti
from juru.parser import Program
from juru.checker import check_source

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


def ok(src):
    """The check must PASS (no exception)."""
    check_source(src)


def expect_check_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected a semantic error, but the check passed")


ALL_KEYWORDS_PROGRAM = (
    'func mix(a) {\n'
    '  if a and not false or null == null {\n'
    '    for i from 0 to 2 {\n'
    '      if i == 1 {\n'
    '        continue\n'
    '      }\n'
    '      while false {\n'
    '        break\n'
    '      }\n'
    '    }\n'
    '  } else {\n'
    '    say("no")\n'
    '  }\n'
    '  return true\n'
    '}\n'
    'say(mix(true))\n'
)

DEMOS = ["demo.jr", "patterns.jr", "table.jr", "funcs_demo.jr",
         "lists_demo.jr", "game_demo.jr", "advanced_demo.jr"]


# ---------- programs that must PASS ----------

def t_ok_empty():
    ok("")


def t_ok_comment_only():
    ok("# nothing here")


def t_ok_simple():
    ok("x = 1\nsay(x)")


def t_ok_builtins_as_calls():
    ok('say(len("ab"))\nsay(int("5"))')


def t_ok_ask_zero_and_one_args():
    ok('ask()\nask("name? ")')


def t_ok_user_func_call():
    ok("func add(a, b) {\n    return a + b\n}\nsay(add(1, 2))")


def t_ok_for_var():
    ok("for i from 1 to 2 {\n    say(i)\n}")


def t_ok_for_var_after_loop():
    ok("for i from 1 to 3 {\n}\nsay(i)")


def t_ok_param_used():
    ok("func f(a) {\n    say(a)\n}")


def t_ok_param_read_by_nested_func():
    """A param is a value too — inner funcs may read it via the parent chain."""
    src = ("func outer(a) {\n"
           "    func inner() {\n"
           "        return a\n"
           "    }\n"
           "    return inner()\n"
           "}\n"
           "say(outer(5))")
    ok(src)


def t_ok_assigned_inside_if_block():
    """Conservative policy: assigned SOMEWHERE is enough for the checker."""
    ok("flag = true\nif flag {\n    x = 1\n}\nsay(x)")


def t_ok_assigned_later_in_program():
    ok("func f() {\n    return x\n}\nx = 5")


def t_ok_local_assign_then_read():
    ok("func f() {\n    x = 1\n    return x\n}\nf()")


def t_ok_setindex_after_assign():
    ok("a = [1]\na[0] = 2")


def t_ok_call_var_holding_func():
    ok("func f() {\n}\ng = f\ng()")


def t_ok_two_defs_different_arity():
    """Two defs for one name → arity is ambiguous → checker stays silent."""
    ok("func f(a) {\n}\nfunc f(a, b) {\n}\nf()")


def t_ok_all_keywords_program():
    ok(ALL_KEYWORDS_PROGRAM)


def t_ok_all_demo_files():
    for name in DEMOS:
        with open(os.path.join(HERE, "examples", name), encoding="utf-8") as f:
            ok(f.read())


def t_policy_conservative_local_assign():
    """Local-only assign → checker allows; the interpreter still guards runtime."""
    ok("func f() {\n    x = 1\n}\nsay(x)")


# ---------- typos die here (before running) ----------

def t_typo_top_level():
    expect_check_galti('name = "JuRu"\nsay(naame)', "'naame' was not found")


def t_typo_inside_func():
    expect_check_galti("func f() {\n    return naame\n}", "was not found")


def t_typo_in_condition():
    expect_check_galti("if ready {\n    say(1)\n}", "'ready' was not found")


def t_typo_in_call_args():
    expect_check_galti("x = 1\nsay(x + 1, sprt(x))", "'sprt' was not found")


def t_typo_index_target():
    expect_check_galti("a[0] = 1", "'a' was not found")


# ---------- reserved names ----------

def t_reserved_assign_len():
    expect_check_galti("len = 5", "'len' is reserved")


def t_reserved_assign_int_deep():
    expect_check_galti("if true {\n    int = 1\n}", "'int' is reserved")


def t_reserved_func_ask():
    expect_check_galti("func ask() {\n}", "'ask' is reserved")


def t_reserved_func_inside_block():
    expect_check_galti("while false {\n    func len() {\n    }\n}", "'len' is reserved")


# ---------- duplicate parameters ----------

def t_dup_params_two():
    expect_check_galti("func f(a, a) {\n}", "'a' twice")


def t_dup_params_three():
    expect_check_galti("func f(a, b, a) {\n}", "'a' twice")


def t_distinct_params_ok():
    ok("func f(a, b, c) {\n    return a + b + c\n}")


# ---------- builtin arity ----------

def t_builtin_arity_len_zero():
    expect_check_galti("say(len())", "len(x) takes exactly 1 argument")


def t_builtin_arity_len_two():
    expect_check_galti("say(len([], []))", "len(x) takes exactly 1 argument")


def t_builtin_arity_ask_two():
    expect_check_galti('say(ask("a", "b"))', "ask(prompt) takes at most 1 argument")


def t_builtin_arity_int_zero():
    expect_check_galti("say(int())", "int(x) takes exactly 1 argument")


def t_builtin_arity_int_two():
    expect_check_galti("say(int(1, 2))", "int(x) takes exactly 1 argument")


# ---------- user func arity ----------

def t_user_arity_few():
    expect_check_galti(
        "func add(a, b) {\n    return a + b\n}\nadd(1)",
        "func 'add' expects 2 arguments, you gave 1")


def t_user_arity_many():
    expect_check_galti(
        "func add(a, b) {\n    return a + b\n}\nadd(1, 2, 3)",
        "func 'add' expects 2 arguments, you gave 3")


def t_user_arity_singular_word():
    expect_check_galti(
        "func f(a) {\n    return a\n}\nf()",
        "func 'f' expects 1 argument, you gave 0")


# ---------- unknown call targets ----------

def t_call_unknown_name():
    expect_check_galti("foo()", "'foo' was not found")


# ---------- precision ----------

def t_error_line_and_col():
    try:
        check_source("a = 1\nb = 2\nsay(c)\n")
    except JuRuGalti as err:
        assert err.line == 3 and err.col == 5, (err.line, err.col)
        return
    raise AssertionError("expected a semantic error")


def t_check_source_returns_program():
    tree = check_source("x = 1")
    assert isinstance(tree, Program)
    assert len(tree.stmts) == 1


# ---------- Step 5: stdlib arity + reserved names ----------

def t_stdlib_arity_upper():
    expect_check_galti("upper(1, 2)", "upper(x) takes exactly 1 argument")


def t_stdlib_arity_push():
    expect_check_galti("push(1)", "push(list, item) takes exactly 2 arguments")
    expect_check_galti("push(1, 2, 3)", "push(list, item) takes exactly 2 arguments")


def t_stdlib_arity_min_max():
    expect_check_galti("min(3)", "min(a, b) takes exactly 2 arguments")
    expect_check_galti("max(1, 2, 3)", "max(a, b) takes exactly 2 arguments")


def t_stdlib_reserved_upper():
    expect_check_galti("upper = 5", "'upper' is reserved (builtin) — pick another name")


# ---------- the pipeline: juru.py must run the checker ----------

def t_juru_pipeline_uses_checker():
    path = os.path.join(HERE, ".tmp_semantic.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write("ghost = 1\nsay(ghsot)\n")   # typo: ghsot
    try:
        out = subprocess.run([sys.executable, "juru.py", path],
                             capture_output=True, text=True)
        assert out.returncode == 1, out
        assert "'ghsot' was not found" in out.stdout, out.stdout
        assert "nothing with this name is ever assigned" in out.stdout
    finally:
        os.remove(path)


# ---------- runner ----------

TESTS = [
    t_ok_empty, t_ok_comment_only, t_ok_simple, t_ok_builtins_as_calls,
    t_ok_ask_zero_and_one_args, t_ok_user_func_call,
    t_ok_for_var, t_ok_for_var_after_loop, t_ok_param_used,
    t_ok_param_read_by_nested_func, t_ok_assigned_inside_if_block,
    t_ok_assigned_later_in_program, t_ok_local_assign_then_read,
    t_ok_setindex_after_assign, t_ok_call_var_holding_func,
    t_ok_two_defs_different_arity, t_ok_all_keywords_program,
    t_ok_all_demo_files, t_policy_conservative_local_assign,
    t_typo_top_level, t_typo_inside_func, t_typo_in_condition,
    t_typo_in_call_args, t_typo_index_target,
    t_reserved_assign_len, t_reserved_assign_int_deep,
    t_reserved_func_ask, t_reserved_func_inside_block,
    t_dup_params_two, t_dup_params_three, t_distinct_params_ok,
    t_builtin_arity_len_zero, t_builtin_arity_len_two,
    t_builtin_arity_ask_two, t_builtin_arity_int_zero,
    t_builtin_arity_int_two,
    t_user_arity_few, t_user_arity_many, t_user_arity_singular_word,
    t_call_unknown_name,
    t_stdlib_arity_upper, t_stdlib_arity_push,
    t_stdlib_arity_min_max, t_stdlib_reserved_upper,
    t_error_line_and_col, t_check_source_returns_program,
    t_juru_pipeline_uses_checker,
]

for test in TESTS:
    check(test.__name__, test)

passed = sum(1 for _, ok_count, _ in RESULTS if ok_count)
failed = [r for r in RESULTS if not r[1]]

print()
print("=" * 50)
print("JuRu Step 3 (Checker): {} pass, {} fail / {} total".format(
    passed, len(failed), len(RESULTS)))
if failed:
    print()
    for name, _, msg in failed:
        print(name + ": " + msg)
    sys.exit(1)
print("Step 3 Checker: ALL PASS ✅")
sys.exit(0)
