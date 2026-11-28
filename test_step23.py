r"""JuRu Step 23 tests — errors you can catch (try / rescue + fail).

The 17 required coverage areas (each pinned, not just "it runs"):
  1.  a rescue catches each supported error kind (math, index, key, value,
      name, loop, input, file, fail)
  2.  e.message carries the EXACT original friendly text
  3.  e.line, e.col and e.kind are correct (pinned values)
  4.  `rescue as e { ... }` works
  5.  plain `rescue { ... }` works (binding optional)
  6.  nested try/rescue behaves predictably (nearest rescue wins)
  7.  fail(message) raises a catchable JuRu error (kind "fail")
  8.  fail() arity/type mistakes give the friendly validation errors
  9.  errors raised inside funcs reach the correct rescue boundary
  10. errors a rescue does not catch propagate normally
  11. uncaught errors keep the EXACT old top-level output (byte-pinned)
  12. call-stack lines are correct for nested function calls
  13. stacks never leak into unrelated errors, never expose host
      tracebacks, never include builtins
  14. the checker rejects bad syntax and bad variable use
  15. rescue scoping: e and rescue locals never leak out
  16. the REPL survives a failed try/rescue and takes the next command
  17. everything OUTSIDE try/rescue is unchanged (language surface,
      dump forms, old programs, version pins)

Plus parser/AST tests (dump forms, both rescue forms, malformed syntax,
empty and nested blocks), the fixed 11-kind table, error values as
values (display, join, ==, members) and module errors keeping kind+stack.
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS, ERROR_KINDS, kind_for
from juru.checker import check_source, BUILTINS
from juru.parser import parse_source, dump
from juru.interpreter import Interpreter
from juru.errfmt import render
from juru.repl import looks_incomplete
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


def run(src, stdin=""):
    tree = check_source(src)
    buf = io.StringIO()
    old_in = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(buf):
            Interpreter().run(tree, base_dir=HERE)
        return buf.getvalue()
    finally:
        sys.stdin = old_in


def caught(src):
    """Run and return the JuRuGalti that escaped the program."""
    try:
        run(src)
    except JuRuGalti as err:
        return err
    raise AssertionError("expected an error: " + src)


def expect_check_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "{} -> {}".format(src, err.message)
        return
    raise AssertionError("expected a semantic error: " + src)


def expect_run_galti(src, fragment):
    err = caught(src)
    assert fragment in err.message, "{} -> {}".format(src, err.message)


def expect_galti(src, fragment):
    expect_check_galti(src, fragment)
    expect_run_galti(src, fragment)


def run_repl(lines):
    proc = subprocess.run(
        [sys.executable, "repl.py"],
        input="\n".join(lines) + "\n",
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    return proc.stdout


def cli(args, input_text=None, cwd=None):
    return subprocess.run(
        [sys.executable, JURU] + args,
        input=input_text, capture_output=True, text=True,
        cwd=cwd or HERE, timeout=120,
    )


# ------------------------------------------------------------------ 1. every kind is catchable
def t_kinds_all_catchable():
    cases = [
        ("math", 'try {\n    say(1 / 0)\n} rescue as e {\n    say(e.kind)\n}'),
        ("index", 'try {\n    say([1, 2, 3][9])\n} rescue as e {\n    say(e.kind)\n}'),
        ("key", 'try {\n    say({"a": 1}["zz"])\n} rescue as e {\n    say(e.kind)\n}'),
        ("value", 'try {\n    n = int("zzz")\n} rescue as e {\n    say(e.kind)\n}'),
        ("loop", 'func boom() {\n    boom()\n}\ntry {\n    boom()\n} rescue as e {\n    say(e.kind)\n}'),
        ("fail", 'try {\n    fail("nope")\n} rescue as e {\n    say(e.kind)\n}'),
    ]
    for kind, src in cases:
        assert run(src) == kind + "\n", (kind, src)
    assert run('try {\n    say(later)\n} rescue as e {\n    say(e.kind)\n}\nlater = 5') == "name\n"


def t_input_kind_catchable():
    out = run('try {\n    x = ask("gimme")\n} rescue as e {\n    say(e.kind + "|" + e.message)\n}',
              stdin="")
    assert "input|ask() could not read any more input" in out, out


def t_file_kind_catchable():
    d = tempfile.mkdtemp(prefix="juru23_")
    try:
        out = run('try {\n    import "nothere.jr"\n} rescue as e {\n    say(e.kind + "|" + e.message)\n}',
                  ) if False else None
        # run with base_dir=d so the import looks next to a file that is not there
        tree = check_source('try {\n    import "nothere.jr"\n} rescue as e {\n    say(e.kind + "|" + e.message)\n}')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            Interpreter().run(tree, base_dir=d)
        assert buf.getvalue().startswith("file|cannot import 'nothere.jr'"), buf.getvalue()
    finally:
        shutil.rmtree(d)


def t_module_error_keeps_kind_and_stack():
    d = tempfile.mkdtemp(prefix="juru23_")
    try:
        with open(os.path.join(d, "bad.jr"), "w", encoding="utf-8") as f:
            f.write('func explode() {\n    say(1 / 0)\n}\nexplode()\n')
        tree = check_source('try {\n    import "bad.jr"\n} rescue as e {\n    say(e.kind + "|" + e.message)\n}')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            Interpreter().run(tree, base_dir=d)
        got = buf.getvalue()
        assert got.startswith("math|in 'bad.jr': cannot divide by zero"), got
        # the same error, uncaught, keeps source_file + stack
        tree = check_source('import "bad.jr"')
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                Interpreter().run(tree, base_dir=d)
        except JuRuGalti as err:
            assert err.kind == "math", err.kind
            assert err.source_file == os.path.join(d, "bad.jr"), err.source_file
            assert err.stack == (("explode", 4),), err.stack
        else:
            raise AssertionError("module error escaped")
    finally:
        shutil.rmtree(d)


# ------------------------------------------------------------------ 2/3. the error value's fields
def t_message_is_the_exact_original_text():
    cases = [
        ("cannot divide by zero (x / 0)", 'say(1 / 0)'),
        ("key 'zz' was not found — this dict has: a", 'say({"a": 1}["zz"])'),
        ("index 9 is out of range — this list has 3 items (0 to 2)", 'say([1, 2, 3][9])'),
    ]
    for message, bomb in cases:
        src = "try {\n    " + bomb + "\n} rescue as e {\n    say(e.message)\n}"
        assert run(src) == message + "\n", (bomb, run(src))


def t_line_col_kind_are_correct():
    got = run('try {\n    say(1 / 0)\n} rescue as e {\n'
              '    say(e.kind + "|" + e.line + "|" + e.col)\n}')
    assert got == "math|2|11\n", got
    got = run('try {\n    d = {"a": 1}\n    say(d["zz"])\n} rescue as e {\n'
              '    say(e.kind + "|" + e.line + "|" + e.col)\n}')
    assert got == "key|3|11\n", got
    got = run('try {\n    say(later)\n} rescue as e {\n'
              '    say(e.kind + "|" + e.line + "|" + e.col)\n}\nlater = 5')
    assert got == "name|2|9\n", got
    got = run('try {\n    n = int("zzz")\n} rescue as e {\n    say(e.kind)\n}')
    assert got == "value\n", got


def t_recursion_error_fields():
    got = run('func boom() {\n    boom()\n}\ntry {\n    boom()\n} rescue as e {\n'
              '    say(e.kind + "|" + e.line + "|" + e.col)\n}')
    assert got == "loop|2|9\n", got


# ------------------------------------------------------------------ 4/5. both rescue forms
def t_rescue_with_binding():
    out = run('try {\n    fail("door stuck")\n} rescue as e {\n'
              '    say("got: " + e.message)\n    say(e.kind)\n}')
    assert out == "got: door stuck\nfail\n", out


def t_rescue_without_binding():
    out = run('try {\n    fail("anything")\n} rescue {\n    say("safe")\n}\nsay("after")')
    assert out == "safe\nafter\n", out


def t_empty_blocks():
    assert run('try {\n} rescue {\n}\nsay("done")') == "done\n"
    assert run('try {\n    say("ok")\n} rescue as e {\n}') == "ok\n"


def t_rescue_on_its_own_line():
    src = ('try {\n'
           '    fail("x")\n'
           '}\n'
           'rescue as e {\n'
           '    say("line break ok: " + e.message)\n'
           '}\n')
    assert run(src) == "line break ok: x\n", run(src)


# ------------------------------------------------------------------ 6. nested try/rescue
def t_nested_nearest_rescue_wins():
    src = ('try {\n'
           '    try {\n'
           '        fail("inner")\n'
           '    } rescue as e {\n'
           '        say("inner caught " + e.message)\n'
           '    }\n'
           '} rescue as e {\n'
           '    say("outer caught " + e.message)\n'
           '}\n')
    assert run(src) == "inner caught inner\n", run(src)


def t_nested_error_in_inner_rescue_reaches_outer():
    src = ('try {\n'
           '    try {\n'
           '        fail("inner")\n'
           '    } rescue as e {\n'
           '        fail("outer-from-inner:" + e.message)\n'
           '    }\n'
           '} rescue as e {\n'
           '    say("outer caught " + e.message)\n'
           '}\n')
    assert run(src) == "outer caught outer-from-inner:inner\n", run(src)


def t_nested_try_inside_rescue():
    src = ('try {\n'
           '    fail("one")\n'
           '} rescue as e {\n'
           '    try {\n'
           '        fail("two")\n'
           '    } rescue {\n'
           '        say("second level safe")\n'
           '    }\n'
           '}\n')
    assert run(src) == "second level safe\n", run(src)


def t_rescue_never_catches_outside_its_try():
    # the try/rescue completes fine; a LATER error still stops the program
    err = caught('try {\n    say("ok")\n} rescue {\n    say("no")\n}\nsay(1 / 0)')
    assert "cannot divide by zero" in err.message, err.message
    assert err.stack is None, err.stack


# ------------------------------------------------------------------ 7. fail()
def t_fail_is_catchable_and_verbatim():
    out = run('try {\n    fail("upstream is down: 503")\n} rescue as e {\n'
              '    say(e.kind + "|" + e.message)\n}')
    assert out == "fail|upstream is down: 503\n", out


def t_fail_kind_wins_over_message_words():
    """fail() passes its kind EXPLICITLY — a user message that merely LOOKS
    like a builtin error must still be kind "fail"."""
    out = run('try {\n    fail("index 9 is out of range — my own rules")\n'
              '} rescue as e {\n    say(e.kind)\n}')
    assert out == "fail\n", out


def t_fail_uncaught_is_a_normal_error():
    err = caught('say("before")\nfail("kaboom")\nsay("never")')
    assert err.message == "kaboom", err.message
    assert err.kind == "fail", err.kind


def t_fail_validation_errors():
    expect_galti("fail()", "fail(message) takes exactly 1 argument")
    expect_galti("fail(1, 2)", "fail(message) takes exactly 1 argument")
    expect_run_galti("fail(5)", "fail() needs a message in quotes — got: int")
    expect_run_galti('fail([1])', "fail() needs a message in quotes — got: list")
    expect_run_galti("fail(null)", "fail() needs a message in quotes — got: null")


def t_fail_inside_func_pinned_line_col():
    got = run('func guard(n) {\n    if n < 0 {\n        fail("negative")\n    }\n'
              '    return n\n}\ntry {\n    guard(-1)\n} rescue as e {\n'
              '    say(e.kind + "|" + e.line + "|" + e.col)\n}')
    assert got == "fail|3|13\n", got          # Call col = the "(" of fail(


# ------------------------------------------------------------------ 9. func boundaries
def t_error_in_func_reaches_top_level_rescue():
    got = run('func risky() {\n    say(1 / 0)\n}\ntry {\n    risky()\n'
              '} rescue as e {\n    say("caught " + e.message)\n}')
    assert got == "caught cannot divide by zero (x / 0)\n", got


def t_func_catches_its_own_error():
    got = run('func safe() {\n'
              '    try {\n'
              '        say(1 / 0)\n'
              '    } rescue as e {\n'
              '        return "handled:" + e.kind\n'
              '    }\n'
              '}\nsay(safe())')
    assert got == "handled:math\n", got


def t_inner_func_error_reaches_outer_func_rescue_not_top():
    src = ('func inner() {\n'
           '    fail("deep")\n'
           '}\n'
           'func outer() {\n'
           '    try {\n'
           '        inner()\n'
           '    } rescue as e {\n'
           '        return "outer handled:" + e.message\n'
           '    }\n'
           '}\n'
           'try {\n'
           '    say(outer())\n'
           '} rescue {\n'
           '    say("WRONG BOUNDARY")\n'
           '}')
    assert run(src) == "outer handled:deep\n", run(src)


def t_arguments_evaluate_in_the_caller():
    """f(1 / 0) — the argument error happens BEFORE the call, so a try
    inside f must not catch it; a try around the call does."""
    src = ('func f(n) {\n'
           '    try {\n'
           '        return "got " + n\n'
           '    } rescue {\n'
           '        return "WRONG: f caught it"\n'
           '    }\n'
           '}\n'
           'try {\n'
           '    f(1 / 0)\n'
           '} rescue as e {\n'
           '    say("caller caught " + e.kind)\n'
           '}')
    assert run(src) == "caller caught math\n", run(src)


def t_call_stack_still_set_for_uncaught_func_errors():
    err = caught('func f() {\n    fail("x")\n}\nf()')
    assert err.stack == (("f", 4),), err.stack


# ------------------------------------------------------------------ 10/11. uncaught = the old output
def t_uncaught_keeps_exact_old_output():
    src_file = tempfile.mkdtemp(prefix="juru23_")
    try:
        prog = os.path.join(src_file, "u1.jr")
        with open(prog, "w", encoding="utf-8") as f:
            f.write("nums = [1, 2, 3]\nsay(nums[7])\n")
        proc = cli([prog], cwd=src_file)
        assert proc.returncode == 1, (proc.returncode, proc.stdout)
        exact = ("JuRu Error (line 2, col 10): index 7 is out of range"
                 " — this list has 3 items (0 to 2)\n"
                 "    say(nums[7])\n"
                 "             ^\n")
        assert proc.stdout == exact, repr(proc.stdout)
        assert "called from" not in proc.stdout
    finally:
        shutil.rmtree(src_file)


def t_uncaught_render_matches_str_prefix():
    err = caught("say(1 / 0)")
    shown = render(err, "say(1 / 0)")
    assert shown.startswith(str(err)), shown
    assert shown.count("\n") == 2, repr(shown)          # header + line + caret
    assert "called from" not in shown


def t_render_fallbacks_keep_stack_but_no_wrong_line():
    err = caught('func f() {\n    fail("x")\n}\nf()')
    assert err.stack is not None
    plain = render(err, None)                            # no source at all
    assert plain.startswith(str(err))
    assert "called from f (line 4)" in plain


# ------------------------------------------------------------------ 12/13. call stacks
def t_stack_tuple_exact_three_deep():
    src = ('func a() {\n    say(1 / 0)\n}\nfunc b() {\n    a()\n}\n'
           'func c() {\n    b()\n}\nc()')
    err = caught(src)
    assert err.stack == (("c", 10), ("b", 8), ("a", 5)), err.stack
    shown = render(err, src)
    assert shown.endswith(
        "called from a (line 5)\ncalled from b (line 8)\ncalled from c (line 10)"), shown
    assert shown.index("called from a") < shown.index("called from b") < shown.index("called from c")


def t_stack_cli_display_three_deep():
    d = tempfile.mkdtemp(prefix="juru23_")
    try:
        prog = os.path.join(d, "u2.jr")
        body = ('func a() {\n    say(1 / 0)\n}\nfunc b() {\n    a()\n}\n'
                'func c() {\n    b()\n}\nc()\n')
        with open(prog, "w", encoding="utf-8") as f:
            f.write(body)
        proc = cli([prog], cwd=d)
        assert proc.returncode == 1
        exact = ("JuRu Error (line 2, col 11): cannot divide by zero (x / 0)\n"
                 "    say(1 / 0)\n"
                 "          ^\n"
                 "called from a (line 5)\n"
                 "called from b (line 8)\n"
                 "called from c (line 10)\n")
        assert proc.stdout == exact, repr(proc.stdout)
    finally:
        shutil.rmtree(d)


def t_builtins_never_appear_in_the_stack():
    err = caught('func g() {\n    say(sorted([1, "a"]))\n}\ng()')
    assert err.stack == (("g", 4),), err.stack


def t_stay_clean_between_unrelated_errors():
    """One interpreter, two runs: the second error's stack is its own."""
    interp = Interpreter()
    first = None
    second = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            interp.run(check_source('func f() {\n    fail("first")\n}\nf()'), base_dir=HERE)
    except JuRuGalti as err:
        first = err
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            interp.run(check_source('func h() {\n    fail("second")\n}\nh()'), base_dir=HERE)
    except JuRuGalti as err:
        second = err
    assert first.stack == (("f", 4),), first.stack
    assert second.stack == (("h", 4),), second.stack
    assert second.message == "second"


def t_top_level_errors_have_no_stack():
    for src in ("say(1 / 0)", "say([1][9])", "x = 1\nsay(x[0])"):
        err = caught(src)
        assert err.stack is None, (src, err.stack)


def t_recursion_stack_exists_for_uncaught():
    err = caught('func boom() {\n    boom()\n}\nboom()')
    assert err.stack is not None and len(err.stack) >= 1, err.stack
    assert err.stack[0] == ("boom", 4), err.stack[0]   # the outermost call site
    assert err.stack[-1] == ("boom", 2), err.stack[-1]  # the deepest call site


def t_signals_pass_through_rescue():
    got = run('for i from 1 to 3 {\n    try {\n        break\n    } rescue {\n'
              '        say("never")\n    }\n}\nsay("broke out")')
    assert got == "broke out\n", got
    got = run('for i from 1 to 3 {\n    try {\n        continue\n    } rescue {\n'
              '        say("never")\n    }\n    say(i)\n}\nsay("done")')
    assert got == "done\n", got                     # continue skips say(i) too
    got = run('func f() {\n    try {\n        return 42\n    } rescue {\n'
              '        return 99\n    }\n}\nsay(f())')
    assert got == "42\n", got


# ------------------------------------------------------------------ 14. the checker
def t_parser_bare_rescue():
    expect_check_galti("rescue {\n    say(1)\n}",
                       "'rescue' needs a matching 'try' before it")
    expect_check_galti("say(1)\nrescue {\n}",
                       "'rescue' needs a matching 'try' before it")


def t_parser_missing_rescue():
    expect_check_galti("try {\n    say(1)\n}\nsay(2)",
                       "a 'try' needs its 'rescue'")


def t_parser_rescue_as_needs_a_name():
    expect_check_galti("try {\n} rescue as {\n}", "'rescue as e' needs a name")
    expect_check_galti("try {\n} rescue as try {\n}",
                       "'try' is a keyword — it cannot be a name")


def t_checker_rescue_reserved_and_undefined():
    expect_check_galti("try {\n} rescue as fail {\n}",
                       "'fail' is reserved (builtin) — pick another name")
    expect_check_galti("try {\n} rescue as e {\n    say(ghost)\n}",
                       "'ghost' was not found")
    expect_check_galti("try {\n    say(ghost)\n} rescue {\n}",
                       "'ghost' was not found")


def t_checker_e_is_usable_inside_rescue():
    tree = check_source('try {\n    fail("x")\n} rescue as e {\n    say(e.message)\n}')
    assert tree is not None


def t_checker_no_name_check_for_fail_args():
    # fail("...") with any text arg is fine; wrong COUNT is refused
    tree = check_source('try {\n    fail("fine")\n} rescue {\n}')
    assert tree is not None


# ------------------------------------------------------------------ 15. rescue scoping
def t_e_does_not_leak_out():
    expect_run_galti('try {\n    fail("x")\n} rescue as e {\n    say(e.message)\n}\nsay(e)',
                     "'e' was not found")


def t_rescue_locals_do_not_leak():
    expect_run_galti('try {\n    fail("x")\n} rescue as e {\n    only = 1\n}\nsay(only)',
                     "'only' was not found")


def t_try_body_assignments_survive():
    assert run('try {\n    n = 5\n} rescue {\n}\nsay(n)') == "5\n"
    assert run('text = "x"\ntry {\n    text = "y"\n} rescue {\n}\nsay(text)') == "y\n"


def t_e_shadowing_is_temporary():
    got = run('e = "outer"\ntry {\n    fail("x")\n} rescue as e {\n'
              '    say("inner sees: " + e.message)\n}\nsay(e)')
    assert got == "inner sees: x\nouter\n", got


def t_error_values_are_values():
    got = run('try {\n    say(1 / 0)\n} rescue as e {\n    say(e)\n}')
    assert got == "<error math: cannot divide by zero (x / 0)>\n", got
    got = run('try {\n    say(1 / 0)\n} rescue as e {\n    say("got: " + e)\n}')
    assert got == "got: <error math: cannot divide by zero (x / 0)>\n", got
    got = run('try {\n    say(1 / 0)\n} rescue as e {\n    say(type(e))\n}')
    assert got == "error\n", got


def t_error_equality_and_members():
    got = run('errs = []\nfor i from 1 to 2 {\n'
              '    try {\n'
              '        fail("same")\n'
              '    } rescue as e {\n'
              '        push(errs, e)\n'
              '    }\n'
              '}\nsay(errs[0] == errs[1])\nsay(errs[0] == "same")')
    assert got == "true\nfalse\n", got
    expect_run_galti('try {\n    fail("x")\n} rescue as e {\n    say(e.foo)\n}',
                     "an error value has message, line, col and kind")


# ------------------------------------------------------------------ 16. the REPL
def t_repl_survives_failed_try_and_takes_next_command():
    out = run_repl([
        "try {",
        "    fail(\"boom\")",
        "} rescue {",
        "    say(\"caught it\")",
        "}",
        "say(\"next works\")",
        "1 + 2",
        "exit",
    ])
    assert "caught it" in out, out
    assert "next works" in out, out
    assert "=> 3" in out, out
    assert "Traceback" not in out, out


def t_repl_multiline_try_with_rescue_prompt():
    out = run_repl([
        "try {",
        "    say(1 / 0)",
        "} rescue as e {",
        "    say(\"safe: \" + e.kind)",
        "}",
        "exit",
    ])
    assert "....> " in out, out          # the block kept the session waiting
    assert "safe: math" in out, out


def t_repl_uncaught_error_then_recovery():
    out = run_repl(["say(1 / 0)", "2 + 2", "exit"])
    assert "cannot divide by zero" in out, out
    assert "=> 4" in out, out


def t_looks_incomplete_heuristic():
    assert looks_incomplete("try { f() }") is True        # rescue still owed
    assert looks_incomplete("try { f() } rescue { }") is False
    assert looks_incomplete("try { f() } rescue as e { }") is False
    assert looks_incomplete('say("try harder")') is False  # text, not a keyword
    assert looks_incomplete("try {") is True
    assert looks_incomplete("} rescue as e {") is True     # braces open
    assert looks_incomplete("rescue { }") is False         # a parse error, not incomplete
    assert looks_incomplete("try { try { fail(1) } rescue { } }") is True   # 2 tries, 1 rescue
    assert looks_incomplete("try { try { fail(1) } rescue { } } rescue { }") is False


# ------------------------------------------------------------------ 17. outside try/rescue unchanged
def t_language_surface_pins():
    assert VERSION == "1.12"
    assert len(KEYWORDS) == 21
    assert "try" in KEYWORDS and "rescue" in KEYWORDS
    assert len(BUILTINS) == 67
    assert "fail" in BUILTINS
    assert ERROR_KINDS == ("name", "type", "value", "arity", "math", "index",
                           "key", "loop", "input", "file", "fail")


def t_kind_classifier():
    assert kind_for("cannot divide by zero (x / 0)") == "math"
    assert kind_for("key 'x' was not found") == "key"
    assert kind_for("index 9 is out of range") == "index"
    assert kind_for("cannot import 'x' — file not found") == "file"
    assert kind_for("ask() could not read any more input") == "input"
    assert kind_for("func 'f' expects 2 arguments, you gave 3") == "arity"
    assert kind_for("'x' was not found") == "name"
    assert kind_for("'x' has no length — only text, lists, dicts and sets do") == "type"
    assert kind_for("something entirely unknown") == "type"
    assert kind_for("anything", explicit="fail") == "fail"     # explicit always wins


def t_dump_forms():
    assert dump(check_source("try { say(1) } rescue as e { say(2) }")) == \
        "(program (try (then (say (num 1))) (rescue e (then (say (num 2))))))"
    assert dump(check_source("try { say(1) } rescue { say(2) }")) == \
        "(program (try (then (say (num 1))) (rescue (then (say (num 2))))))"
    tree = check_source("try {\n    say(1)\n}\n\nrescue as e {\n    say(2)\n}")
    assert isinstance(tree.stmts[0].__class__.__name__, str)
    assert dump(tree) == "(program (try (then (say (num 1))) (rescue e (then (say (num 2))))))"


def t_old_programs_unchanged():
    # programs that never use try/rescue run exactly as before
    assert run('say("hello, " + "world")\nfor i from 1 to 3 {\n    say(i * 2)\n}') == \
        "hello, world\n2\n4\n6\n"
    assert run('nums = [3, 1, 2]\nsay(sorted(nums))\nsay(nums[0:2])') == "[1, 2, 3]\n[3, 1]\n"
    expect_run_galti("y = 1\ny = y / 0", "cannot divide by zero (x / 0)")


def t_old_error_display_unchanged():
    # the Step 17 layout: message, source line, caret — nothing added
    err = caught("say(1 / 0)")
    shown = render(err, "say(1 / 0)")
    lines = shown.splitlines()
    assert len(lines) == 3, lines
    assert lines[0] == str(err)
    assert lines[1] == "    say(1 / 0)"
    assert lines[2] == "          ^"


# ------------------------------------------------------------------ runner
ALL = [
    ("kinds: math/index/key/value/loop/fail all catchable", t_kinds_all_catchable),
    ("kind input catchable (ask at end of input)", t_input_kind_catchable),
    ("kind file catchable (missing module)", t_file_kind_catchable),
    ("module error keeps kind + stack + source file", t_module_error_keeps_kind_and_stack),
    ("e.message is the exact original text", t_message_is_the_exact_original_text),
    ("e.line / e.col / e.kind are correct", t_line_col_kind_are_correct),
    ("recursion error fields (kind loop)", t_recursion_error_fields),
    ("rescue as e works", t_rescue_with_binding),
    ("plain rescue works", t_rescue_without_binding),
    ("empty try/rescue blocks", t_empty_blocks),
    ("rescue may sit on its own line", t_rescue_on_its_own_line),
    ("nested: nearest rescue wins", t_nested_nearest_rescue_wins),
    ("nested: error in inner rescue reaches outer", t_nested_error_in_inner_rescue_reaches_outer),
    ("nested try inside a rescue block", t_nested_try_inside_rescue),
    ("rescue never catches outside its try", t_rescue_never_catches_outside_its_try),
    ("fail() is catchable, message verbatim", t_fail_is_catchable_and_verbatim),
    ("fail() kind wins over message words", t_fail_kind_wins_over_message_words),
    ("uncaught fail() is a normal error", t_fail_uncaught_is_a_normal_error),
    ("fail() validation errors (checker + runtime)", t_fail_validation_errors),
    ("fail() inside func: pinned line/col", t_fail_inside_func_pinned_line_col),
    ("func error reaches the top-level rescue", t_error_in_func_reaches_top_level_rescue),
    ("a func catches its own error", t_func_catches_its_own_error),
    ("inner func error handled by outer func's rescue", t_inner_func_error_reaches_outer_func_rescue_not_top),
    ("arguments evaluate in the caller", t_arguments_evaluate_in_the_caller),
    ("uncaught func errors still record the stack", t_call_stack_still_set_for_uncaught_func_errors),
    ("uncaught CLI output byte-pinned (no stack lines)", t_uncaught_keeps_exact_old_output),
    ("uncaught render keeps the old 3-line shape", t_uncaught_render_matches_str_prefix),
    ("render fallback adds only the stack lines", t_render_fallbacks_keep_stack_but_no_wrong_line),
    ("stack tuple exact, three calls deep", t_stack_tuple_exact_three_deep),
    ("stack display via the CLI, byte-pinned", t_stack_cli_display_three_deep),
    ("builtins never appear in the stack", t_builtins_never_appear_in_the_stack),
    ("stacks stay clean between unrelated errors", t_stay_clean_between_unrelated_errors),
    ("top-level errors carry no stack", t_top_level_errors_have_no_stack),
    ("recursion: the recorded stack exists", t_recursion_stack_exists_for_uncaught),
    ("break/continue/return pass through rescue", t_signals_pass_through_rescue),
    ("parser: bare rescue refused", t_parser_bare_rescue),
    ("parser: try without rescue refused", t_parser_missing_rescue),
    ("parser: rescue as needs a name", t_parser_rescue_as_needs_a_name),
    ("checker: reserved + undefined in rescue blocks", t_checker_rescue_reserved_and_undefined),
    ("checker: e is usable inside the rescue", t_checker_e_is_usable_inside_rescue),
    ("checker: fail args are not name-checked", t_checker_no_name_check_for_fail_args),
    ("e does not leak out of the rescue", t_e_does_not_leak_out),
    ("rescue locals do not leak out", t_rescue_locals_do_not_leak),
    ("try body assignments survive", t_try_body_assignments_survive),
    ("e shadowing is temporary", t_e_shadowing_is_temporary),
    ("error values display, join and type()", t_error_values_are_values),
    ("error equality + unknown members", t_error_equality_and_members),
    ("REPL survives a failed try/rescue", t_repl_survives_failed_try_and_takes_next_command),
    ("REPL multi-line try + rescue prompt", t_repl_multiline_try_with_rescue_prompt),
    ("REPL uncaught error then recovery", t_repl_uncaught_error_then_recovery),
    ("looks_incomplete: try/rescue heuristic", t_looks_incomplete_heuristic),
    ("language surface pins (21/67/1.12/kinds)", t_language_surface_pins),
    ("kind classifier rules", t_kind_classifier),
    ("dump forms (both rescue shapes)", t_dump_forms),
    ("old programs run unchanged", t_old_programs_unchanged),
    ("old error display unchanged", t_old_error_display_unchanged),
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
