"""JuRu Step 4 tests — Interpreter: math, types, loops, funcs, lists, errors,
plus every demo file verified against its EXACT output."""
import builtins
import contextlib
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti
from juru.interpreter import run_source

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
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()


def run_file(name):
    with open(os.path.join(HERE, "examples", "test", name), encoding="utf-8") as f:
        return run(f.read())


def expect_run_galti(src, fragment):
    try:
        run(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected an error, but the code ran fine")


# ---------- math: add / subtract / multiply / divide / modulo ----------

def t_math_basic():
    out = run("say(5 + 3)\nsay(10 - 4)\nsay(6 * 7)\nsay(10 / 4)\nsay(7 % 3)")
    assert out == "8\n6\n42\n2.5\n1\n", repr(out)


def t_math_float():
    out = run("say(2.5 + 1)\nsay(1.5 * 2)\nsay(10.0 / 4)\nsay(0.5 + 0.25)")
    assert out == "3.5\n3.0\n2.5\n0.75\n", repr(out)


def t_math_auto_promote():
    """int + float = float; / is always true division."""
    out = run("say(1 + 2.5)\nsay(10 / 2)\nsay(2.0)")
    assert out == "3.5\n5.0\n2.0\n", repr(out)


def t_math_precedence():
    out = run("say(2 + 3 * 4)\nsay((2 + 3) * 4)\nsay(10 - 2 - 3)\nsay(2 * 3 % 4)")
    assert out == "14\n20\n5\n2\n", repr(out)


def t_math_negative():
    out = run("say(-5 + 2)\nsay(10 - -3)")
    assert out == "-3\n13\n", repr(out)


def t_math_big():
    out = run("say(999999 * 999999)")
    assert out == "999998000001\n", repr(out)


def t_float_display():
    """IEEE-754 reality, shown honestly (no magic)."""
    out = run("say(0.1 + 0.2)")
    assert out == "0.30000000000000004\n", repr(out)


# ---------- text powers (friendly like Python) ----------

def t_str_concat_auto():
    out = run('say("ab" + "cd")\nsay("n = " + 42)\nsay("pi = " + 3.14)\nsay(1 + "a")')
    assert out == "abcd\nn = 42\npi = 3.14\n1a\n", repr(out)


def t_str_repeat():
    assert run('say("ab" * 3)') == "ababab\n"


def t_str_repeat_zero():
    assert run('say("ab" * 0)\nsay("")') == "\n\n"


def t_str_index_and_len():
    out = run('say("hello"[1])\nsay(len("hello"))')
    assert out == "e\n5\n", repr(out)


def t_str_compare():
    out = run('say("apple" < "banana")\nsay("a" == "a")')
    assert out == "true\ntrue\n", repr(out)


# ---------- bool / null ----------

def t_bool_output():
    out = run("say(3 > 2)\nsay(2 == 3)\nsay(true and false)\nsay(not true)\nsay(true or false)")
    assert out == "true\nfalse\nfalse\nfalse\ntrue\n", repr(out)


def t_equals_categories():
    """true != 1 (different categories), but 1 == 1.0 (same number family)."""
    out = run('say(true == 1)\nsay(1 == 1.0)\nsay("a" == "a")\nsay(null == null)')
    assert out == "false\ntrue\ntrue\ntrue\n", repr(out)


def t_short_circuit_safe():
    """1 / 0 never even runs — and/or short-circuit."""
    out = run('if false and 1 / 0 == 1 { say("x") } else { say("safe") }')
    assert out == "safe\n", repr(out)
    out = run('if true or 1 / 0 == 1 { say("also safe") }')
    assert out == "also safe\n", repr(out)


def t_truthy_rules():
    out = run('say(not 0)\nsay(not "")\nsay(not [1])\nsay(not null)')
    assert out == "true\ntrue\nfalse\ntrue\n", repr(out)
    out = run('if "" {\n  say("ran")\n} else {\n  say("skipped")\n}')
    assert out == "skipped\n", repr(out)


# ---------- variables & scoping ----------

def t_vars():
    out = run("x = 10\nx = x + 5\nsay(x)\ny = x * 2\nsay(y)")
    assert out == "15\n30\n", repr(out)


def t_scoping_shadow():
    """Assignment inside a func is local — globals stay untouched."""
    src = ("x = 1\n"
           "func f() {\n"
           "    x = 99\n"
           "    return x\n"
           "}\n"
           "say(f())\n"
           "say(x)")
    assert run(src) == "99\n1\n"


def t_scoping_read_parent():
    src = ("x = 10\n"
           "func f() {\n"
           "    return x + 5\n"
           "}\n"
           "say(f())")
    assert run(src) == "15\n"


def t_hinglish_names_run():
    src = "bolo = 1\nagar2 = 2\nsay(bolo + agar2)"
    assert run(src) == "3\n"


# ---------- decisions ----------

def t_if_elif_else():
    src = ('n = 7\n'
           'if n > 10 {\n  say("big")\n} else if n > 5 {\n  say("medium")\n'
           '} else {\n  say("small")\n}')
    assert run(src) == "medium\n"


# ---------- loops ----------

def t_while():
    src = "i = 0\nwhile i < 3 {\n    say(i)\n    i = i + 1\n}"
    assert run(src) == "0\n1\n2\n"


def t_for_inclusive():
    assert run("for i from 1 to 5 {\n  say(i)\n}") == "1\n2\n3\n4\n5\n"


def t_for_downward():
    """start > end → the loop counts down (inclusive both ends)."""
    assert run("for i from 3 to 1 {\n  say(i)\n}") == "3\n2\n1\n"


def t_for_downward_negative():
    assert run("for i from 1 to -2 {\n  say(i)\n}") == "1\n0\n-1\n-2\n"


def t_for_single():
    assert run("for i from 2 to 2 {\n  say(i)\n}") == "2\n"


def t_for_var_visible_after():
    src = "for i from 1 to 3 {\n}\nsay(i)"
    assert run(src) == "3\n"


def t_continue():
    src = "for i from 1 to 6 {\n    if i % 2 == 0 {\n        continue\n    }\n    say(i)\n}"
    assert run(src) == "1\n3\n5\n"


def t_break():
    src = "for i from 1 to 10 {\n    if i == 4 {\n        break\n    }\n    say(i)\n}"
    assert run(src) == "1\n2\n3\n"


def t_break_while():
    src = ("n = 0\n"
           "while true {\n"
           "    n = n + 1\n"
           "    if n == 3 {\n"
           "        break\n"
           "    }\n"
           "}\n"
           "say(n)")
    assert run(src) == "3\n"


def t_nested_loop_break():
    """break only leaves its OWN loop."""
    src = ("for i from 1 to 3 {\n"
           "    for j from 1 to 3 {\n"
           "        if j == 2 {\n"
           "            break\n"
           "        }\n"
           "        say(i + \"-\" + j)\n"
           "    }\n"
           "}")
    assert run(src) == "1-1\n2-1\n3-1\n"


def t_for_needs_int():
    expect_run_galti("for i from 1 to 2.5 { }", "whole numbers")


# ---------- funcs + recursion ----------

def t_factorial():
    src = ("func factorial(n) {\n"
           "    if n <= 1 {\n"
           "        return 1\n"
           "    }\n"
           "    return n * factorial(n - 1)\n"
           "}\n"
           "say(factorial(5))\n"
           "say(factorial(10))")
    assert run(src) == "120\n3628800\n"


def t_factorial_12():
    src = ("func factorial(n) {\n"
           "    if n <= 1 {\n"
           "        return 1\n"
           "    }\n"
           "    return n * factorial(n - 1)\n"
           "}\n"
           "say(factorial(12))")
    assert run(src) == "479001600\n"


def t_fibo():
    src = ("func fibo(n) {\n"
           "    if n <= 1 {\n"
           "        return n\n"
           "    }\n"
           "    return fibo(n - 1) + fibo(n - 2)\n"
           "}\n"
           "for i from 1 to 10 {\n"
           "    say(fibo(i))\n"
           "}")
    assert run(src) == "1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n"


def t_return_null():
    src = "func f() {\n    return\n}\nsay(f())"
    assert run(src) == "null\n"


def t_no_return_null():
    src = "func f() {\n}\nsay(f())"
    assert run(src) == "null\n"


def t_func_as_value():
    src = "func f() {\n}\nsay(f)"
    assert run(src) == "<func f>\n"


def t_args_count_error():
    src = "func add(a, b) {\n    return a + b\n}\nadd(1)"
    expect_run_galti(src, "expects 2 arguments")


def t_recursion_depth_error():
    src = "func f(n) {\n    return f(n + 1)\n}\nf(0)"
    expect_run_galti(src, "recursion")


def t_call_non_func():
    src = "x = 5\nx()"
    expect_run_galti(src, "cannot be called")


# ---------- lists ----------

def t_list_ops():
    src = ('a = [1, 2, 3]\n'
           'say(a)\n'
           'say(a[1])\n'
           'a[2] = 99\n'
           'say(a)\n'
           'say(len(a))\n'
           'say([1] + [2])')
    assert run(src) == "[1, 2, 3]\n2\n[1, 2, 99]\n3\n[1, 2]\n"


def t_list_concat_vars():
    src = "a = [1, 2]\nb = [3]\nsay(a + b)"
    assert run(src) == "[1, 2, 3]\n"


def t_list_of_mixed():
    assert run('say(["a", 1, true, null])') == "[a, 1, true, null]\n"


def t_list_bounds_error():
    src = "a = [1]\nsay(a[5])"
    expect_run_galti(src, "out of range")


def t_negative_index_error():
    src = "a = [1, 2]\nsay(a[-1])"
    expect_run_galti(src, "out of range")


def t_index_type_error():
    src = 'a = [1, 2]\nsay(a["1"])'
    expect_run_galti(src, "whole number")


def t_grid_setindex():
    src = ("grid = [[1, 2], [3, 4]]\n"
           "grid[1][0] = 7\n"
           "say(grid)")
    assert run(src) == "[[1, 2], [7, 4]]\n"


def t_setindex_on_text():
    src = 's = "abc"\ns[0] = "x"'
    expect_run_galti(src, "only lists and dicts support")


def t_text_repeat_cap():
    """'ab' * huge used to leak a Python MemoryError — now a friendly error."""
    expect_run_galti('say("ab" * 999999999999)',
                     "text cannot grow over 10,000,000 characters")
    assert run('say("ab" * 3)') == "ababab\n"
    expect_run_galti('say("ab" * -1)', "needs a whole number (0 or more)")


def t_compare_type_guards():
    """Different worlds refuse ordering — no Python TypeError ever leaks."""
    expect_run_galti("say(1 < null)", "cannot compare int and null")
    expect_run_galti("say([1] < [2])", "cannot compare list and list")
    expect_run_galti('say({} < {})', "cannot compare dict and dict")
    expect_run_galti("say(true < true)", "cannot compare bool and bool")
    expect_run_galti('say("a" < 1)', "cannot compare text and int")
    assert run('say("a" < "b")\nsay(2 > 1)\nsay(1 <= 1.0)') == "true\ntrue\ntrue\n"


def t_arith_type_guards():
    expect_run_galti('say("a" - "b")', "'-' only works on numbers")
    expect_run_galti("say(-[1])", "'-' does not work on list")
    expect_run_galti("say(null + 1)", "cannot use '+' on null and int")
    expect_run_galti("say({} + {})", "cannot use '+' on dict and dict")
    expect_run_galti('say([1] * "a")', "'*' only works on numbers")
    expect_run_galti('say("ab" * "a")', "text * number needs a whole number")
    expect_run_galti("say(true + 1)", "cannot use '+' on bool and int")
    expect_run_galti('say("a" % 2)', "'%' only works on numbers")
    assert run('say("a" + true)\nsay(null == null)') == "atrue\ntrue\n"


# ---------- builtins ----------

def t_len_errors():
    expect_run_galti("say(len(5))", "has no length")


def t_int_builtin():
    out = run('say(int("42"))\nsay(int(2.9))')
    assert out == "42\n2\n", repr(out)


def t_int_bad():
    expect_run_galti('say(int("abc"))', "is not a whole number")


def t_int_bool_error():
    expect_run_galti("say(int(true))", "cannot be converted")


def t_reserved_names():
    expect_run_galti("len = 5", "reserved")
    expect_run_galti("func ask() {\n}", "reserved")


def t_ask_input():
    orig = builtins.input
    builtins.input = lambda prompt="": "25"
    try:
        out = run('age = int(ask("age? "))\nsay("next year: " + (age + 1))')
    finally:
        builtins.input = orig
    assert out == "next year: 26\n", repr(out)


def t_ask_no_prompt():
    orig = builtins.input
    builtins.input = lambda prompt="": "hi"
    try:
        out = run("say(ask())")
    finally:
        builtins.input = orig
    assert out == "hi\n", repr(out)


def t_say_variants():
    out = run('say(1, 2)\nsay()\nsay(null)\nsay([1, "two"])')
    assert out == "1 2\n\nnull\n[1, two]\n", repr(out)


# ---------- runtime errors (friendly + safe) ----------

def t_div_zero():
    expect_run_galti("say(1 / 0)", "cannot divide by zero")


def t_mod_zero():
    expect_run_galti("say(5 % 0)", "with zero")


def t_undefined_var():
    expect_run_galti("say(x)", "was not found")


def t_bool_math_error():
    expect_run_galti("say(true + 1)", "cannot use '+'")


def t_mixed_compare_error():
    expect_run_galti('say(1 < "a")', "cannot compare")


def t_list_plus_text_error():
    expect_run_galti('say([1] + "a")', "cannot be joined with text")


def t_old_bolo_hint():
    expect_run_galti("bolo(1)", "(the old 'bolo' is now 'say')")


# ---------- advanced algorithms (next level) ----------

def t_matrix_3d_sum():
    src = ("g = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]\n"
           "total = 0\n"
           "for i from 0 to 1 {\n"
           "    for j from 0 to 1 {\n"
           "        for k from 0 to 1 {\n"
           "            total = total + g[i][j][k]\n"
           "        }\n"
           "    }\n"
           "}\n"
           "say(total)")
    assert run(src) == "36\n"


def t_count_vowels():
    src = ('word = "programming"\n'
           'tally = 0\n'
           'for i from 0 to len(word) - 1 {\n'
           '    ch = word[i]\n'
           '    if ch == "a" or ch == "e" or ch == "i" or ch == "o" or ch == "u" {\n'
           '        tally = tally + 1\n'
           '    }\n'
           '}\n'
           'say(tally)')
    assert run(src) == "3\n"


def t_find_max():
    src = ("nums = [4, 17, 2, 99, 23, 8]\n"
           "best = nums[0]\n"
           "for i from 1 to len(nums) - 1 {\n"
           "    if nums[i] > best {\n"
           "        best = nums[i]\n"
           "    }\n"
           "}\n"
           "say(best)")
    assert run(src) == "99\n"


def t_linear_search():
    src = ("nums = [10, 20, 30, 40]\n"
           "found = -1\n"
           "for i from 0 to len(nums) - 1 {\n"
           "    if nums[i] == 30 {\n"
           "        found = i\n"
           "    }\n"
           "}\n"
           "say(found)")
    assert run(src) == "2\n"


def t_reverse_list_in_place():
    src = ("nums = [1, 2, 3, 4, 5]\n"
           "i = 0\n"
           "j = len(nums) - 1\n"
           "while i < j {\n"
           "    temp = nums[i]\n"
           "    nums[i] = nums[j]\n"
           "    nums[j] = temp\n"
           "    i = i + 1\n"
           "    j = j - 1\n"
           "}\n"
           "say(nums)")
    assert run(src) == "[5, 4, 3, 2, 1]\n"


def t_collatz_steps():
    """6 → 3 → 10 → 5 → 16 → 8 → 4 → 2 → 1 (8 steps)."""
    src = ("n = 6\n"
           "steps = 0\n"
           "while n != 1 {\n"
           "    if n % 2 == 0 {\n"
           "        n = n / 2\n"
           "    } else {\n"
           "        n = 3 * n + 1\n"
           "    }\n"
           "    steps = steps + 1\n"
           "}\n"
           "say(steps)")
    assert run(src) == "8\n"


def t_gcd():
    src = ("func gcd(a, b) {\n"
           "    while b != 0 {\n"
           "        temp = b\n"
           "        b = a % b\n"
           "        a = temp\n"
           "    }\n"
           "    return a\n"
           "}\n"
           "say(gcd(48, 18))")
    assert run(src) == "6\n"


def t_power_func():
    src = ("func power(base, exp) {\n"
           "    result = 1\n"
           "    for i from 1 to exp {\n"
           "        result = result * base\n"
           "    }\n"
           "    return result\n"
           "}\n"
           "say(power(2, 10))")
    assert run(src) == "1024\n"


def t_digit_sum():
    src = ("n = 9876\n"
           "total = 0\n"
           "while n > 0 {\n"
           "    total = total + n % 10\n"
           "    n = int(n / 10)\n"
           "}\n"
           "say(total)")
    assert run(src) == "30\n"


def t_sum_1_to_100():
    src = ("total = 0\n"
           "for i from 1 to 100 {\n"
           "    total = total + i\n"
           "}\n"
           "say(total)")
    assert run(src) == "5050\n"


def t_nested_func_calls():
    src = ("func twice(x) {\n"
           "    return x * 2\n"
           "}\n"
           "func add(a, b) {\n"
           "    return a + b\n"
           "}\n"
           "say(add(twice(3), twice(4)))")
    assert run(src) == "14\n"


def t_func_early_return():
    src = ("func find_first_even(nums) {\n"
           "    for i from 0 to len(nums) - 1 {\n"
           "        if nums[i] % 2 == 0 {\n"
           "            return nums[i]\n"
           "        }\n"
           "    }\n"
           "    return -1\n"
           "}\n"
           "say(find_first_even([7, 3, 8, 5]))\n"
           "say(find_first_even([1, 3, 5]))")
    assert run(src) == "8\n-1\n"


def t_fibo_15():
    src = ("func fibo(n) {\n"
           "    if n <= 1 {\n"
           "        return n\n"
           "    }\n"
           "    return fibo(n - 1) + fibo(n - 2)\n"
           "}\n"
           "say(fibo(15))")
    assert run(src) == "610\n"


def t_scope_dynamic_read():
    """Funcs read globals dynamically — they see the LATEST value."""
    src = ("x = 5\n"
           "func f() {\n"
           "    return x\n"
           "}\n"
           "x = 7\n"
           "say(f())")
    assert run(src) == "7\n"


def t_param_shadows_global():
    src = ("x = 1\n"
           "func f(x) {\n"
           "    return x + 100\n"
           "}\n"
           "say(f(5))\n"
           "say(x)")
    assert run(src) == "105\n1\n"


def t_multiplication_grid():
    src = ("for i from 1 to 3 {\n"
           "    row = \"\"\n"
           "    for j from 1 to 3 {\n"
           "        row = row + i * j + \" \"\n"
           "    }\n"
           "    say(row)\n"
           "}")
    assert run(src) == "1 2 3 \n2 4 6 \n3 6 9 \n"


def t_string_build_loop():
    src = ('out = ""\n'
           'for i from 1 to 5 {\n'
           '    out = out + i + "-"\n'
           '}\n'
           'say(out)')
    assert run(src) == "1-2-3-4-5-\n"


# ---------- demo files — EXACT output verification ----------

def t_demo_jr():
    assert run_file("demo.jr") == "hello JuRu!\nLevel 3\n8\n2.5\n1\n5.0\n5.0\n"


def t_patterns_jr():
    square = "* * * * * \n" * 5
    tri = "* \n" + "* * \n" + "* * * \n" + "* * * * \n" + "* * * * * \n"
    pyr = "    *\n   ***\n  *****\n *******\n*********\n"
    assert run_file("patterns.jr") == square + "\n" + tri + "\n" + pyr


def t_table_jr():
    expected = "".join("7 x {} = {}\n".format(i, 7 * i) for i in range(1, 11))
    assert run_file("table.jr") == expected


def t_funcs_demo_jr():
    expected = ("factorial:\n"
                "1! = 1\n2! = 2\n3! = 6\n4! = 24\n5! = 120\n6! = 720\n7! = 5040\n"
                "fibonacci:\n"
                "1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n")
    assert run_file("funcs_demo.jr") == expected


def t_lists_demo_jr():
    assert run_file("lists_demo.jr") == "3\nmango\n[apple, mango, apple]\ntotal: 245\n"


def t_game_demo_jr():
    expected = ("Round 1: Boss HP -> 90\n"
                "Boss dealt 25! HP -> 75\n"
                "Round 2: Boss HP -> 70\n"
                "Boss dealt 25! HP -> 50\n"
                "Round 3: Boss HP -> 40\n"
                "Boss dealt 25! HP -> 25\n"
                "Round 4: Boss HP -> 0\n"
                "BOSS DOWN! You win!\n")
    assert run_file("game_demo.jr") == expected


def t_advanced_demo_jr():
    expected = (
        "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n"
        "2\n3\n5\n7\n11\n13\n17\n19\n"
        "[11, 12, 22, 25, 64]\n"
        "[[1, 9], [3, 4]]\n"
        "grid total: 17\n"
        "level is a palindrome!\n"
        "T-minus 5\nT-minus 4\nT-minus 3\nT-minus 1\n"
        "LIFTOFF!\n")
    assert run_file("advanced_demo.jr") == expected


# ---------- the .jr runner itself ----------

def t_runner_needs_jr():
    out = subprocess.run([sys.executable, "juru.py", "notes.txt"],
                         cwd=HERE, capture_output=True, text=True)
    assert out.returncode == 1, out
    assert "'.jr'" in out.stdout


def t_runner_runs_file():
    out = subprocess.run([sys.executable, "juru.py", "examples/test/demo.jr"],
                         cwd=HERE, capture_output=True, text=True)
    assert out.returncode == 0, out
    assert out.stdout.startswith("hello JuRu!\n")


# ---------- runner ----------

TESTS = [
    t_math_basic, t_math_float, t_math_auto_promote, t_math_precedence,
    t_math_negative, t_math_big, t_float_display,
    t_str_concat_auto, t_str_repeat, t_str_repeat_zero,
    t_str_index_and_len, t_str_compare,
    t_bool_output, t_equals_categories, t_short_circuit_safe, t_truthy_rules,
    t_vars, t_scoping_shadow, t_scoping_read_parent, t_hinglish_names_run,
    t_if_elif_else,
    t_while, t_for_inclusive, t_for_downward, t_for_downward_negative,
    t_for_single, t_for_var_visible_after, t_continue, t_break,
    t_break_while, t_nested_loop_break, t_for_needs_int,
    t_factorial, t_factorial_12, t_fibo, t_return_null, t_no_return_null,
    t_func_as_value, t_args_count_error, t_recursion_depth_error,
    t_call_non_func,
    t_list_ops, t_list_concat_vars, t_list_of_mixed, t_list_bounds_error,
    t_negative_index_error, t_index_type_error, t_grid_setindex,
    t_setindex_on_text,
    t_text_repeat_cap,
    t_compare_type_guards,
    t_arith_type_guards,
    t_len_errors, t_int_builtin, t_int_bad, t_int_bool_error,
    t_reserved_names, t_ask_input, t_ask_no_prompt, t_say_variants,
    t_div_zero, t_mod_zero, t_undefined_var, t_bool_math_error,
    t_mixed_compare_error, t_list_plus_text_error, t_old_bolo_hint,
    t_matrix_3d_sum, t_count_vowels, t_find_max, t_linear_search,
    t_reverse_list_in_place, t_collatz_steps, t_gcd, t_power_func,
    t_digit_sum, t_sum_1_to_100, t_nested_func_calls, t_func_early_return,
    t_fibo_15, t_scope_dynamic_read, t_param_shadows_global,
    t_multiplication_grid, t_string_build_loop,
    t_demo_jr, t_patterns_jr, t_table_jr, t_funcs_demo_jr,
    t_lists_demo_jr, t_game_demo_jr, t_advanced_demo_jr,
    t_runner_needs_jr, t_runner_runs_file,
]

for test in TESTS:
    check(test.__name__, test)

passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = [r for r in RESULTS if not r[1]]

print()
print("=" * 50)
print("JuRu Step 4 (Interpreter): {} pass, {} fail / {} total".format(
    passed, len(failed), len(RESULTS)))
if failed:
    print()
    for name, _, msg in failed:
        print(name + ": " + msg)
    sys.exit(1)
print("Step 4 Interpreter: ALL PASS ✅")
sys.exit(0)
