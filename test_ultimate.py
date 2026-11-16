"""JuRu ULTIMATE test — steps 1–9 combined, no mercy.

Every feature from every step in ONE file:
  1 lexer (19 keywords)  2 parser  3 checker  4 interpreter
  5 stdlib + REPL        6 dicts/for-in/in/slices/strings/math
  7 modules (import)     8 did-you-mean + multi-line REPL
  9 stdlib wave 2: sorted / reverse / find / keys / values / count

Rule of the game: no test may trust another layer. Programs are run
through the real checker AND the real CLI AND the real REPL.
"""
import contextlib
import io
import json
import os
import random as pyrandom
import re
import shutil
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.parser import parse_source
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
from juru.interpreter import Interpreter
from juru.version import VERSION

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


def run(src, base_dir=None, seed=None):
    """checker → interpreter → stdout text."""
    if seed is not None:
        pyrandom.seed(seed)
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=base_dir)
    return buf.getvalue()


def expect_galti(src, fragment, base_dir=None):
    try:
        run(src, base_dir=base_dir)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected an error, but the program ran: " + src)


def expect_check_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected a semantic error, but the check passed")


def run_repl(lines):
    proc = subprocess.run(
        [sys.executable, "repl.py"],
        input="\n".join(lines) + "\n",
        capture_output=True, text=True, cwd=HERE, timeout=120,
    )
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    return proc.stdout


def scratch(files):
    d = tempfile.mkdtemp(prefix="juru_ultimate_")
    for name, content in files.items():
        target = os.path.join(d, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
    return d


# ================================================================ 1+6+7 combined
def t_all_19_keywords_one_program():
    """All 19 keywords + dict + for-in + in/not-in + import in ONE program."""
    module_src = (
        "func boost(n) {\n"                         # func, return
        "    if n < 0 {\n"
        "        return 0\n"
        "    }\n"
        "    return n * 2\n"
        "}\n"
        "magic = 10\n"
    )
    d = scratch({"helpers.jr": module_src})
    src = (
        'import "helpers.jr"\n'                     # import
        'score = 0\n'
        'for w in ["a", "b", "c", "d"] {\n'         # for, in
        '    if w == "b" {\n'                       # if
        '        continue\n'                        # continue
        '    }\n'
        '    if w == "d" {\n'
        '        break\n'                           # break
        '    }\n'
        '    score = score + 1\n'
        '}\n'
        'n = 0\n'
        'while score > 0 and not false {\n'         # while, and, not, false
        '    score = score - 1\n'
        '    if score == null or true {\n'          # null, or, true
        '        n = n + 1\n'
        '    } else {\n'                            # else
        '        break\n'
        '    }\n'
        '}\n'
        'if n == 1 {\n'
        '    say("one")\n'
        '} else {\n'
        '    say("not one")\n'
        '}\n'
        'for i from 1 to 2 {\n'                     # from, to
        '    score = score + helpers.magic\n'
        '}\n'
        'total = helpers.boost(21) + n + score\n'
        'words = split("x,y", ",")\n'
        'if "y" in words and "z" not in words {\n'  # in, not in
        '    total = total + len(words)\n'
        '}\n'
        'say(total)\n'
        'say(total > 0 and not (total < 0) or false)\n'
    )
    for kw in KEYWORDS:                             # every one of the 19
        assert re.search(r"\b" + kw + r"\b", src + module_src), "missing: " + kw
    assert len(KEYWORDS) == 19
    out = run(src, base_dir=d)
    assert out == "not one\n66\ntrue\n", out
    shutil.rmtree(d)


def t_final_boss_program():
    """THE combined program: module + dict + for-in + slices + strings +
    while + break + in/not-in + funcs → exact story output."""
    src = (
        'import "examples/test/helpers.jr"\n'
        '\n'
        'report = {}\n'
        'words = split(trim("  fire ice fire bolt fire ice  "), " ")\n'
        'for w in words {\n'
        '    if w in report {\n'
        '        report[w] = report[w] + 1\n'
        '    } else {\n'
        '        report[w] = 1\n'
        '    }\n'
        '}\n'
        'say(report)\n'
        'say("top: " + report["fire"])\n'
        '\n'
        'best = 0\n'
        'for k in report {\n'
        '    if report[k] > best {\n'
        '        best = report[k]\n'
        '    }\n'
        '}\n'
        'say("best count: " + best)\n'
        '\n'
        'team = ["Aman", "Riya", "Kabir"]\n'
        'say("team slice: " + join(team[1:3], " & "))\n'
        'if "Riya" in team and "Zara" not in team {\n'
        '    say("roster ok")\n'
        '}\n'
        '\n'
        'label = ""\n'
        'for i from 1 to 3 {\n'
        '    label = label + helpers.greet(team[i - 1]) + " | "\n'
        '    if i == 2 {\n'
        '        continue\n'
        '    }\n'
        '}\n'
        'say(trim(label))\n'
        '\n'
        'hp = 10\n'
        'while hp > 0 {\n'
        '    hp = hp - 3\n'
        '    if hp == 4 {\n'
        '        break\n'
        '    }\n'
        '}\n'
        'say("hp: " + hp)\n'
        'say(helpers.double(best))\n'
        'say(helpers.magic)\n'
        'say(report["fire"] not in [0])\n'
    )
    out = run(src, base_dir=HERE)
    assert out == (
        "{fire: 3, ice: 2, bolt: 1}\n"
        "top: 3\n"
        "best count: 3\n"
        "team slice: Riya & Kabir\n"
        "roster ok\n"
        "hello Aman! | hello Riya! | hello Kabir! |\n"
        "hp: 4\n"
        "6\n"
        "42\n"
        "true\n"
    ), out


# ================================================================ dicts torture
def t_word_frequency_torture():
    src = (
        'counts = {}\n'
        'for w in split("the cat saw the dog and the dog saw the cat", " ") {\n'
        '    if w in counts {\n'
        '        counts[w] = counts[w] + 1\n'
        '    } else {\n'
        '        counts[w] = 1\n'
        '    }\n'
        '}\n'
        'for word in counts {\n'
        '    say(word + " -> " + counts[word])\n'
        '}\n'
        'say("different words: " + len(counts))\n'
        'say(counts["the"] == 4 and counts["and"] == 1)\n'
        'say("the" in counts and "zzz" not in counts)\n'
    )
    assert run(src) == (
        "the -> 4\n"
        "cat -> 2\n"
        "saw -> 2\n"
        "dog -> 2\n"
        "and -> 1\n"
        "different words: 5\n"
        "true\n"
        "true\n"
    )


def t_memoized_fibo():
    """Dict as a cache — fibo(25) would take ~240k calls without it."""
    src = (
        'stats = {"calls": 0}\n'
        'cache = {1: 1, 2: 1}\n'
        'func fibo(n) {\n'
        '    stats["calls"] = stats["calls"] + 1\n'
        '    if n in cache {\n'
        '        return cache[n]\n'
        '    }\n'
        '    answer = fibo(n - 1) + fibo(n - 2)\n'
        '    cache[n] = answer\n'
        '    return answer\n'
        '}\n'
        'say(fibo(25))\n'
        'say(stats["calls"])\n'
        'say(len(cache))\n'
        'say(fibo(20))\n'
        'func fact(n) {\n'
        '    if n <= 1 {\n'
        '        return 1\n'
        '    }\n'
        '    return n * fact(n - 1)\n'
        '}\n'
        'say(fact(15))\n'
    )
    assert run(src) == "75025\n47\n25\n6765\n1307674368000\n"


def t_dict_trap_combo():
    """Downward for builds a dict; slicing it is the trap."""
    src = (
        'seq = []\n'
        'for i from 5 to 1 {\n'
        '    push(seq, i)\n'
        '}\n'
        'say(seq)\n'
        'once = 0\n'
        'for i from 3 to 3 {\n'
        '    once = once + 1\n'
        '}\n'
        'say(once)\n'
        'd = {}\n'
        'for i from 3 to 1 {\n'
        '    d[i] = i * 10\n'
        '}\n'
        'say(d)\n'
        'say(d[2])\n'
        'say(seq[1:3])\n'
    )
    assert run(src) == "[5, 4, 3, 2, 1]\n1\n{3: 30, 2: 20, 1: 10}\n20\n[4, 3]\n"
    expect_galti('d = {3: 30, 2: 20, 1: 10}\nsay(d[1:2])',
                 "slices work on lists and text — got: {3: 30, 2: 20, 1: 10}")


def t_truthiness_matrix():
    lines = [
        ("null", "n"), ("false", "n"), ("0", "n"), ("0.0", "n"),
        ('""', "n"), ("[]", "n"), ("{}", "n"),
        ("1", "T"), ("-1", "T"), ("0.5", "T"), ('"a"', "T"),
        ("[0]", "T"), ('{"k": 0}', "T"), ('"false"', "T"),
    ]
    src = "\n".join(
        'if {} {{ say("T") }} else {{ say("n") }}'.format(expr)
        for expr, _ in lines
    ) + "\n"
    assert run(src) == "\n".join(want for _, want in lines) + "\n"


def t_type_matrix():
    """Every type through display, len, in, index, equality — one law for all."""
    src = (
        'say(null)\n'
        'say(true)\n'
        'say(false)\n'
        'say(7)\n'
        'say(2.5)\n'
        'say("text")\n'
        'say([1, "a", null])\n'
        'say({"a": 1, "b": [true]})\n'
        'say(len("hello"))\n'
        'say(len([1, 2, 3]))\n'
        'say(len({"a": 1, "b": 2, "c": 3}))\n'
        'say(1 == 1.0)\n'
        'say(true == 1)\n'
        'say("1" == 1)\n'
        'say(null == null)\n'
        'say([1, [2]] == [1, [2.0]])\n'
        'say({"a": [1]} == {"a": [1.0]})\n'
        'say({"a": 1} != {"a": 2})\n'
        'say([1, 2, 3][1])\n'
        'say("hello"[1])\n'
        'say({"k": [10, 20]}["k"][0])\n'
        'say(2 in [1, 2, 3])\n'
        'say("ell" in "hello")\n'
        'say("a" in {"a": 1})\n'
        'say([1, 2] in [[1, 2], [3]])\n'
    )
    assert run(src) == (
        "null\n"
        "true\n"
        "false\n"
        "7\n"
        "2.5\n"
        "text\n"
        "[1, a, null]\n"
        "{a: 1, b: [true]}\n"
        "5\n"
        "3\n"
        "3\n"
        "true\n"
        "false\n"
        "false\n"
        "true\n"
        "true\n"
        "true\n"
        "true\n"
        "2\n"
        "e\n"
        "10\n"
        "true\n"
        "true\n"
        "true\n"
        "true\n"
    )


# ================================================================ loops stress
def t_for_in_stress_10000():
    src = (
        'total = 0\n'
        'for i from 1 to 10000 {\n'
        '    total = total + i\n'
        '}\n'
        'say(total)\n'
        'nums = []\n'
        'j = 0\n'
        'while j < 10000 {\n'
        '    push(nums, j)\n'
        '    j = j + 1\n'
        '}\n'
        't2 = 0\n'
        'for x in nums {\n'
        '    t2 = t2 + x\n'
        '}\n'
        'say(t2)\n'
        'say(len(nums))\n'
    )
    assert run(src) == "50005000\n49995000\n10000\n"


def t_prime_sieve():
    """Eratosthenes — lists, index writes, nested while, from/to."""
    src = (
        'limit = 30\n'
        'sieve = []\n'
        'for i from 0 to limit {\n'
        '    push(sieve, true)\n'
        '}\n'
        'sieve[0] = false\n'
        'sieve[1] = false\n'
        'n = 2\n'
        'while n * n <= limit {\n'
        '    if sieve[n] {\n'
        '        mark = n * n\n'
        '        while mark <= limit {\n'
        '            sieve[mark] = false\n'
        '            mark = mark + n\n'
        '        }\n'
        '    }\n'
        '    n = n + 1\n'
        '}\n'
        'found = []\n'
        'for i from 2 to limit {\n'
        '    if sieve[i] {\n'
        '        push(found, i)\n'
        '    }\n'
        '}\n'
        'say(found)\n'
        'say(len(found))\n'
        'say(29 in found)\n'
        'say(15 in found)\n'
    )
    assert run(src) == (
        "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n"
        "10\n"
        "true\n"
        "false\n"
    )


# ================================================================ strings
def t_slice_string_pipeline():
    src = (
        'raw = "  Hello, JuRu, World!  "\n'
        'clean = trim(raw)\n'
        'parts = split(clean, ", ")\n'
        'first = parts[0]\n'
        'say(upper(first))\n'
        'say(lower(first))\n'
        'say(first[1:3])\n'
        'say(replace(first, "l", "L"))\n'
        'say(join(parts, " | "))\n'
        'say("ell" in first)\n'
        'say(len(parts))\n'
        'say(parts[2][0:5])\n'
        'say(str(42) + str(1.5) + str(true))\n'
        'say(int("7") + int(2.9))\n'
    )
    assert run(src) == (
        "HELLO\n"
        "hello\n"
        "el\n"
        "HeLLo\n"
        "Hello | JuRu | World!\n"
        "true\n"
        "3\n"
        "World\n"
        "421.5true\n"
        "9\n"
    )


# ================================================================ random
def t_random_dice_torture():
    src = (
        'lo = 99\n'
        'hi = 0\n'
        'for i from 1 to 200 {\n'
        '    n = random(1, 6)\n'
        '    if n < lo {\n'
        '        lo = n\n'
        '    }\n'
        '    if n > hi {\n'
        '        hi = n\n'
        '    }\n'
        '}\n'
        'say(lo)\n'
        'say(hi)\n'
    )
    assert run(src, seed=7) == "1\n6\n"
    expect_galti("random(6, 1)", "in random(low, high), low cannot be bigger than high (6 > 1)")
    expect_galti("random(1.5, 6)", "random() needs whole numbers — got: 1.5")
    expect_galti("random(1, 6.5)", "random() needs whole numbers — got: 6.5")


def t_dungeon_game_seeded():
    """while + break + dict inventory + random, fully deterministic with a seed."""
    src = (
        'hp = 20\n'
        'potions = {"small": 2, "big": 1}\n'
        'waves = 0\n'
        'while hp > 0 and waves < 3 {\n'
        '    waves = waves + 1\n'
        '    hit = random(1, 6)\n'
        '    hp = hp - hit\n'
        '    if hp <= 0 {\n'
        '        break\n'
        '    }\n'
        '    if "small" in potions and potions["small"] > 0 {\n'
        '        potions["small"] = potions["small"] - 1\n'
        '        hp = hp + 4\n'
        '    }\n'
        '}\n'
        'say("waves: " + waves)\n'
        'say("hp: " + hp)\n'
        'say(potions)\n'
    )
    assert run(src, seed=7) == "waves: 3\nhp: 19\n{small: 0, big: 1}\n"


# ================================================================ modules
def t_module_chain_runs_once():
    """a → b → c; main imports in REVERSE order — each file still runs once."""
    d = scratch({
        "a.jr": 'say("loading a")\nvalue_a = 1\n',
        "b.jr": 'import "a.jr"\nsay("loading b")\nvalue_b = 2\n',
        "c.jr": 'import "b.jr"\nsay("loading c")\nfunc triple(n) {\n    return n * 3\n}\n',
    })
    src = (
        'import "c.jr"\n'
        'import "b.jr"\n'
        'import "a.jr"\n'
        'say(c.triple(7))\n'
        'say(b.value_b + a.value_a)\n'
    )
    assert run(src, base_dir=d) == (
        "loading a\n"
        "loading b\n"
        "loading c\n"
        "21\n"
        "3\n"
    )
    shutil.rmtree(d)


def t_module_readonly_and_errors():
    src = 'import "examples/test/helpers.jr"\nsay(helpers)\n'
    assert run(src, base_dir=HERE) == "<module helpers>\n"
    expect_galti('import "examples/test/helpers.jr"\nsay(helpers.nope)',
                 "'helpers' has no 'nope' — the module has: double, greet, magic",
                 base_dir=HERE)
    expect_check_galti('import "examples/test/helpers.jr"\nhelpers.magic = 5',
                       "'data.key = value' does not work")


def t_error_gauntlet():
    """Every big error message of steps 4–7, exact fragments, in one go."""
    expect_galti('d = {"a": 1}\nsay(d["z"])',
                 "key 'z' was not found — this dict has: a")
    expect_galti("say([1, 2, 3][0:2:0])",
                 "the slice step cannot be zero")
    expect_galti('split("a", "")', "the split separator cannot be empty")
    expect_galti('replace("a", "", "b")', "the old text cannot be empty in replace()")
    expect_galti("sqrt(-1)", "sqrt(-1) — a negative number has no square root")
    expect_galti('say({"a": 1}[1.5])', "a dict key must be text or a whole number — got: 1.5")
    expect_galti('for x in 5 { say(x) }',
                 "'for x in ...' needs a list, text, dict, or set — got: 5")
    expect_galti('say(5 in 5)', "'in' needs a list, text, dict, or set on the right — got: 5")
    expect_galti('d = {}\nd.name = 1', "'data.key = value' does not work")
    expect_galti('s = "abc"\ns[0] = "x"', "only lists and dicts support item assignment")
    # import errors need a real base dir
    d = scratch({
        "loop_a.jr": 'import "loop_b.jr"\n',
        "loop_b.jr": 'import "loop_a.jr"\n',
        "selfy.jr": 'import "selfy.jr"\n',
        "broken.jr": "func f() {\n    return ghsot\n}\n",
    })
    expect_galti('import "missing.jr"',
                 "cannot import 'missing.jr' — file not found", base_dir=d)
    expect_galti('import "loop_a.jr"',
                 "import loop: loop_a.jr -> loop_b.jr -> loop_a.jr", base_dir=d)
    expect_galti('import "selfy.jr"',
                 "import loop: selfy.jr -> selfy.jr", base_dir=d)
    expect_galti('import "broken.jr"',
                 "in 'broken.jr': 'ghsot' was not found", base_dir=d)
    shutil.rmtree(d)


def t_checker_before_runtime():
    """The checker speaks BEFORE a single line runs — dead code included."""
    import contextlib as _cl
    # case 1: an unknown name kills the whole program — nothing prints
    buf = io.StringIO()
    try:
        with _cl.redirect_stdout(buf):
            run('say("you will never see this")\nsay(ghost_name)\n')
    except JuRuGalti as err:
        assert "ghost_name" in err.message, err.message
    else:
        raise AssertionError("checker allowed an unknown name")
    assert buf.getvalue() == "", "output escaped the checker: " + repr(buf.getvalue())
    # case 2: wrong builtin arity inside a func nobody calls
    buf = io.StringIO()
    try:
        with _cl.redirect_stdout(buf):
            run('func dead() {\n    say(sqrt(1, 2, 3))\n}\n')
    except JuRuGalti as err:
        assert "sqrt(x) takes exactly 1 argument" in err.message, err.message
    else:
        raise AssertionError("checker allowed sqrt(1, 2, 3)")
    assert buf.getvalue() == ""
    # case 3: `{` at statement start gets the friendly dict hint
    expect_check_galti('{ "a": 1 }',
                       "a dict needs a home: write 'data = { ... }'")


# ================================================================ security audit
def t_reserved_audit():
    assert len(BUILTINS) == 47
    wave1 = {"split", "join", "trim", "replace", "abs", "round", "random", "sqrt"}
    wave2 = {"sorted", "reverse", "find", "keys", "values", "count"}
    wave3 = {"float", "pow", "pop", "type"}
    wave4 = {"help", "sleep"}
    wave22 = {"insert", "remove_at", "clear", "extend", "unique",
              "delete", "items", "merge", "index_of", "starts_with",
              "ends_with", "ord", "chr", "set_of", "union", "intersect",
              "difference"}
    assert wave1 <= set(BUILTINS)
    assert wave2 <= set(BUILTINS)
    assert wave3 <= set(BUILTINS)
    assert wave4 <= set(BUILTINS)
    assert wave22 <= set(BUILTINS)
    for name in BUILTINS:
        expect_check_galti("{} = 1".format(name),
                           "'{}' is reserved (builtin) — pick another name".format(name))
        expect_check_galti(
            "func {}(a) {{\n    return a\n}}".format(name),
            "'{}' is reserved (builtin) — pick another name".format(name))
    assert len(KEYWORDS) == 19          # steps 8–22 added zero keywords
    assert {"in", "import"} <= set(KEYWORDS)


def t_mirror_rule_full():
    """Wrong arity: checker message == runtime message == hint, for every builtin."""
    for name, (lo, hi) in BUILTIN_ARITY.items():
        hint = BUILTIN_HINT[name]
        calls = []
        if lo > 0:                      # too few (ask()/help() with none is legal)
            inner = ", ".join(["1"] * (lo - 1))
            calls.append("{}({})".format(name, inner))
        if hi is not None:
            calls.append("{}({})".format(name, ", ".join(["1"] * (hi + 1))))   # too many
        else:                           # variadic: only zero args is wrong
            calls.append("{}()".format(name))
        for call in calls:
            expect_check_galti(call, hint)
            expect_galti(call, hint)


def t_all_15_examples_via_cli():
    names = sorted(os.listdir(os.path.join(HERE, "examples", "test")))
    assert len(names) == 15, "expected 15 examples, got: " + str(names)
    for name in names:
        if not name.endswith(".jr"):
            continue
        proc = subprocess.run(
            [sys.executable, "juru.py", os.path.join("examples", "test", name)],
            capture_output=True, text=True, cwd=HERE, timeout=60,
        )
        assert proc.returncode == 0, "{} failed:\n{}{}".format(
            name, proc.stdout, proc.stderr)


def t_checker_approves_all_examples():
    for folder in ("test", "guide"):
        for name in sorted(os.listdir(os.path.join(HERE, "examples", folder))):
            if not name.endswith(".jr"):
                continue
            with open(os.path.join(HERE, "examples", folder, name),
                      encoding="utf-8") as f:
                src = f.read()
            check_source(src)           # raises on any semantic mistake


def t_repl_dict_import_torture():
    out = run_repl([
        'import "examples/test/helpers.jr"',
        'd = {"a": 1}',
        'd["b"] = 2',
        'd',
        'say(helpers.double(21))',
        '"ell" in "hello"',
        'for x in [1, 2] { say(x) }',
        'trim("  x  ")',
        '5 = 3',
        'say("still alive")',
        'exit',
    ])
    clean = []
    for ln in out.splitlines():
        ln = ln.replace("....> ", "").replace("juru> ", "")
        if ln in ("juru>", "....>"):
            ln = ""
        if ln:
            clean.append(ln)
    text = "\n".join(clean)
    assert clean[0].startswith("JuRu " + VERSION), out
    assert "=> {a: 1, b: 2}" in clean, text
    assert "42" in clean, text
    assert "=> true" in clean, text
    assert "1" in clean and "2" in clean, text
    assert "=> x" in clean, text
    assert any("one statement per line" in ln for ln in clean), text
    assert "still alive" in clean, text   # the session survived the error


# ================================================================ step 8: did-you-mean
def t_did_you_mean_gauntlet():
    """Every typo surface gets the closest real name — and a hopeless typo
    stays plain (never a wrong guess)."""
    # checker surfaces
    try:
        check_source('name = "JuRu"\nsay(naame)')
    except JuRuGalti as err:
        assert "did you mean 'name'?" in err.message, err.message
    else:
        raise AssertionError("checker missed the typo")
    try:
        check_source('func total(n) {\n    return n\n}\nsay(tota(5))')
    except JuRuGalti as err:
        assert "did you mean 'total'?" in err.message, err.message
    else:
        raise AssertionError("checker missed the call typo")
    try:
        check_source('say(le("abc"))')
    except JuRuGalti as err:
        assert "did you mean 'len'?" in err.message, err.message
    else:
        raise AssertionError("checker missed the builtin typo")
    try:
        check_source("say(bolo)")
    except JuRuGalti as err:
        assert "(the old 'bolo' is now 'say')" in err.message, err.message
        assert "did you mean" not in err.message, err.message
    else:
        raise AssertionError("checker missed the old keyword")
    # hopeless typo = no suggestion, plain message
    try:
        check_source('qzwxec = 1\nsay(rvbytn)')
    except JuRuGalti as err:
        assert "did you mean" not in err.message, err.message
    else:
        raise AssertionError("checker should still reject the typo")
    # runtime surfaces
    try:
        run('d = {"score": 1, "lives": 9}\nsay(d["scorr"])')
    except JuRuGalti as err:
        assert "did you mean 'score'?" in err.message, err.message
    else:
        raise AssertionError("runtime missed the dict-key typo")
    try:
        run('import "examples/test/helpers.jr"\nsay(helpers.duble(2))')
    except JuRuGalti as err:
        assert "did you mean 'double'?" in err.message, err.message
    else:
        raise AssertionError("runtime missed the member typo")


def t_typo_top_of_recursion_hell():
    """The suggestion must not slow the checker down or break deep programs:
    40 funcs with near-identical names, every call site typo'd."""
    lines = []
    for i in range(40):
        lines.append("func worker_{}(n) {{\n    return n + 1\n}}".format(i))
    lines.append("say(worker_99(1))")     # worker_0..39 exist, 99 does not
    try:
        check_source("\n".join(lines))
    except JuRuGalti as err:
        assert "did you mean 'worker_9'?" in err.message, err.message
    else:
        raise AssertionError("checker missed the typo")


# ================================================================ step 9: stdlib wave 2
def t_top_words_pipeline():
    """The flag-ship combo: split + count + keys + sorted + find together —
    count the words of a text and rank them."""
    src = (
        'text = "go go stop go wait go stop wait go"\n'
        'words = split(text, " ")\n'
        'rank = {"go": 0, "stop": 0, "wait": 0}\n'
        'for w in keys(rank) {\n'
        '    rank[w] = count(words, w)\n'
        '}\n'
        'order = reverse(sorted(keys(rank)))\n'
        'for w in order {\n'
        '    say(w + " = " + rank[w])\n'
        '}\n'
        'say(find(words, "wait"))\n'
        'say(find(words, "nope") == -1)\n'
    )
    assert run(src) == (
        "wait = 2\n"
        "stop = 2\n"
        "go = 5\n"
        "4\n"
        "true\n"
    )


def t_step9_guard_wall():
    """Every wrong value gets the same friendly wall at runtime."""
    walls = [
        ("sorted(5)", "sorted() needs a list — got: 5"),
        ('sorted("ab")', "sorted() needs a list — got: ab"),
        ('sorted([1, "a"])',
         "sorted() needs a list of only numbers or only text — got: [1, a]"),
        ("reverse(5)", "reverse() needs a list — got: 5"),
        ("find(5, 1)", "find() needs a list first — got: 5"),
        ("keys([1])", "keys() needs a dict — got: [1]"),
        ("values(5)", "values() needs a dict — got: 5"),
        ("count(5, 1)", "count() needs a list first — got: 5"),
    ]
    for src, fragment in walls:
        expect_galti(src, fragment)


def t_step9_purity_never_mutates():
    """sorted/reverse leave the original alone; push is still the only mutator."""
    assert run(
        "a = [3, 1, 2]\n"
        "b = sorted(a)\n"
        "c = reverse(a)\n"
        "d = reverse(sorted(a))\n"
        "say(a)\n"
        "say(b == [1, 2, 3])\n"
        "say(c == [2, 1, 3])\n"
        "say(d == [3, 2, 1])\n"
    ) == "[3, 1, 2]\ntrue\ntrue\ntrue\n"


def t_final_boss_batch1():
    """The FINAL BOSS of batch 1: steps 1–9 in one program — a leaderboard
    of player scores with dicts, modules, sorting, counting and a while."""
    src = (
        'import "examples/test/helpers.jr"\n'
        'scores = {"ada": 88, "bo": 95, "cy": 61, "dee": 88}\n'
        'names = sorted(keys(scores))\n'
        'best = ""\n'
        'top = -1\n'
        'for n in names {\n'
        '    s = scores[n]\n'
        '    if s > top {\n'
        '        top = s\n'
        '        best = n\n'
        '    }\n'
        '}\n'
        'say("winner: " + best + " with " + top)\n'
        'say("runners-up: " + count(values(scores), 88))\n'
        'say(helpers.double(50) - top)\n'
        'say("sorted scores: " + str(sorted(values(scores))))\n'
        'say("reverse: " + str(reverse(sorted(values(scores)))))\n'
        'say("dee at rank: " + str(find(sorted(values(scores)), 88) == 1))\n'
    )
    assert run(src) == (
        "winner: bo with 95\n"
        "runners-up: 2\n"
        "5\n"
        "sorted scores: [61, 88, 88, 95]\n"
        "reverse: [95, 88, 88, 61]\n"
        "dee at rank: true\n"
    )


# ================================================================ step 8+9: REPL
def t_repl_multiline_session():
    """A real session: blocks across lines, ....> prompts, echoes, recovery."""
    out = run_repl([
        'for i from 1 to 4 {',
        '    if i == 2 {',
        '        continue',
        '    }',
        '    say(i)',
        '}',
        'nums = [5, 3, 9]',
        'sorted(nums)',
        'count([1, 1, 2], 1)',
        'say(find(nums, 9))',
        'd = {',
        '    "a": 1,',
        '    "b": 2',
        '}',
        'keys(d)',
        'say(sorted([1, "a"]))',      # runtime guard fires mid-session
        'say("still alive")',
        'exit',
    ])
    clean = []
    for ln in out.splitlines():
        ln = ln.replace("....> ", "").replace("juru> ", "")
        if ln in ("juru>", "....>"):
            ln = ""
        if ln:
            clean.append(ln)
    text = "\n".join(clean)
    assert "1" in clean and "3" in clean and "4" in clean, text
    assert "=> [3, 5, 9]" in clean, text
    assert "=> 2" in clean, text
    assert "2" in clean, text              # say(find(nums, 9)) -> 2
    assert "=> [a, b]" in clean, text     # keys(d) echoes; assignments do not
    assert "needs a list of only numbers or only text" in text, text
    assert "still alive" in clean, text
    assert "....>" in out                 # the continuation prompt was shown


def t_repl_new_builtins_live():
    """The 6 new tools work in the REPL too — checker sees earlier lines."""
    out = run_repl([
        'data = [4, 1, 3]',
        'say(sorted(data))',
        'say(reverse(data))',
        'say(find(data, 3))',
        'd = {"x": 1, "y": 2}',
        'say(keys(d))',
        'say(values(d))',
        'say(count(data, 4))',
        'exit',
    ])
    clean = []
    for ln in out.splitlines():
        ln = ln.replace("....> ", "").replace("juru> ", "")
        if ln in ("juru>", "....>"):
            ln = ""
        if ln:
            clean.append(ln)
    text = "\n".join(clean)
    assert "[1, 3, 4]" in clean, text
    assert "[3, 1, 4]" in clean, text      # reverse of [4, 1, 3]
    assert "2" in clean, text
    assert "[x, y]" in clean, text
    assert "[1, 2]" in clean, text
    assert "1" in clean, text


# ================================================================ batch 2/3/4: version + language surface
def t_batch4_version_bump():
    assert VERSION == "1.9"
    from juru.lexer import KEYWORDS
    from juru.checker import BUILTINS
    assert len(KEYWORDS) == 19          # Step 22 added zero keywords
    assert len(BUILTINS) == 47          # 24 + wave3 (4) + wave4 (help, sleep) + Step 22 (17)


def t_templates_end_to_end():
    """--new a quiz, feed it answers through the real CLI, exact output."""
    import tempfile
    d = tempfile.mkdtemp(prefix="juru_ult_")
    made = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py"), "--new", "ultquiz", "quiz"],
        capture_output=True, text=True, cwd=d, timeout=60,
    )
    assert made.returncode == 0, made.stdout + made.stderr
    ran = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py"), os.path.join(d, "ultquiz.jr")],
        input="4\nParis\n.jr\n", capture_output=True, text=True, cwd=d, timeout=60,
    )
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert ran.stdout == (
        "What is 2 + 2?\n"
        "your answer: correct!\n"
        "Capital of France?\n"
        "your answer: correct!\n"
        "JuRu files end with...?\n"
        "your answer: correct!\n"
        "score: 3/3\n"
        "perfect!\n"
    ), ran.stdout


def t_new_refusal_gauntlet():
    """Every wrong --new gets a friendly no, and nothing is created."""
    import tempfile
    d = tempfile.mkdtemp(prefix="juru_ult_")
    cases = [
        (["--new", "bad name"], "not a usable program name"),
        (["--new", "1abc"], "not a usable program name"),
        (["--new", "../escape"], "not a usable program name"),
        (["--new", "x", "zzzzzz"], "no template 'zzzzzz'"),
        (["--new", "x", "qiz"], "did you mean 'quiz'?"),
    ]
    for args, fragment in cases:
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "juru.py")] + args,
            capture_output=True, text=True, cwd=d, timeout=60,
        )
        assert proc.returncode == 1, (args, proc.stdout)
        assert fragment in proc.stdout, (args, proc.stdout)
    assert os.listdir(d) == [], "refused --new calls must create nothing"


def t_templates_listing_complete():
    proc = subprocess.run(
        [sys.executable, "juru.py", "--templates"],
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for name in ("starter", "calculator", "quiz", "guessing_game", "word_stats"):
        assert name in proc.stdout, name


def t_tutorial_graduation_program():
    """The tutorial's final program, run straight from the markdown."""
    import re
    with open(os.path.join(HERE, "docs", "tutorial.md"), encoding="utf-8") as f:
        text = f.read()
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "```jr":
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                body.append(lines[i])
                i += 1
            blocks.append("\n".join(body))
        i += 1
    graduation = blocks[-1]
    assert "counts" in graduation and "winner" in graduation, "graduation block lost"
    assert run(graduation) == (
        "total words: 9\n"
        "unique words: 6\n"
        "winner: the (3 times)\n"
        "[and, cat, cat, dog, ran, saw, the, the, the]\n"
    )


# ================================================================ batch 3: stdlib wave 3 + packaging + editor
def t_batch3_wave3_builtins_live():
    """float/pow/pop/type, live through the real pipeline."""
    assert run("say(float(\"3.5\") + int(\"1\"))") == "4.5\n"
    assert run("say(pow(2, 8))") == "256\n"
    assert run("stack = [\"x\", \"y\"]\nsay(pop(stack))\nsay(len(stack))") == "y\n1\n"
    assert run("say(type(2.5) == \"float\")") == "true\n"
    expect_galti("say(pow(0, -2))", "0 cannot be raised to a negative power")
    expect_galti("say(pop([]))", "this list is empty")


def t_batch3_repl_subcommand():
    """python3 juru.py repl is now an official way in."""
    proc = subprocess.run(
        [sys.executable, "juru.py", "repl"],
        input="say(6 * 7)\nexit\n", capture_output=True, text=True,
        cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "JuRu {} (easy like Python".format(VERSION) in proc.stdout
    assert "juru> 42" in proc.stdout, proc.stdout


def t_batch3_calculator_float_session():
    """The calculator template now speaks decimals, end to end."""
    proc = subprocess.run(
        [sys.executable, "juru.py", "src/juru/templates/calculator.jr"],
        input="2.5 * 2\n0.1 + 0.2\n1 / 3\nexit\n",
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "> = 5.0" in proc.stdout, proc.stdout
    assert "> = 0.30000000000000004" in proc.stdout, proc.stdout
    assert "> = 0.3333333333333333" in proc.stdout, proc.stdout


def t_batch3_package_and_editor():
    """The pyproject is present, the grammar matches, the launcher answers."""
    import tomllib
    with open(os.path.join(HERE, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["name"] == "juru"
    assert data["project"]["scripts"]["juru"] == "juru.cli:main"
    proc = subprocess.run(
        [sys.executable, "juru.py", "--version"],
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.stdout.strip() == "JuRu " + VERSION, proc.stdout
    import json
    with open(os.path.join(HERE, "vscode", "juru-vscode",
                           "syntaxes", "juru.tmLanguage.json"),
              encoding="utf-8") as f:
        grammar = json.load(f)
    pattern = grammar["repository"]["keywords"]["match"]
    assert "while" in pattern and "func" in pattern, pattern


# ================================================================ batch 4: help + sleep + bare REPL + caret errors
def t_batch4_help_and_sleep_live():
    assert run("help(\"pow\")").startswith("pow(a, b)")
    assert run("help()").startswith("JuRu toolbox — 19 keywords + 47 builtins")
    assert run('say(type(sleep(0)))') == "null\n"
    expect_galti("say(sleep(-1))", "cannot go back in time")
    expect_galti("say(sleep(99))", "at most 30 seconds at a time")


def t_batch4_helpdb_is_truthful():
    """Cards == the real language tables; overview names everything."""
    from juru import helpdb
    assert set(helpdb.BUILTIN_CARDS) == set(BUILTINS)
    assert set(helpdb.KEYWORD_CARDS) == set(KEYWORDS)
    text = helpdb.overview()
    for name in BUILTINS:
        assert name in text
    for kw in KEYWORDS:
        assert kw in text


def t_batch4_caret_errors_via_cli():
    """The CLI now shows the line + caret under the exact column."""
    import tempfile
    d = tempfile.mkdtemp(prefix="juru_ult_")
    path = os.path.join(d, "oops.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write("nums = [1, 2, 3]\nsay(nums[7])\n")
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py"), path],
        capture_output=True, text=True, cwd=d, timeout=60,
    )
    assert proc.returncode == 1, proc.stdout
    assert "index 7 is out of range" in proc.stdout
    lines = proc.stdout.splitlines()
    code = [ln for ln in lines if "say(nums[7])" in ln][0]
    caret = [ln for ln in lines if "^" in ln][0]
    # both rendered lines carry the same 4-space indent, so the caret sits
    # exactly under the offending index "7" at the same index
    assert caret.index("^") == code.index("7"), (code, caret)
    assert "Traceback" not in proc.stderr


def t_batch4_bare_command_is_repl():
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py")],
        input="help\nexit\n", capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.startswith("JuRu {} (".format(VERSION)), proc.stdout
    assert "JuRu toolbox — 19 keywords + 47 builtins" in proc.stdout


# ================================================================ batch 5: the standalone interpreter + the run button
def t_batch5_frozen_build_files():
    """The PyInstaller spec + entry + install note exist and agree."""
    spec = open(os.path.join(HERE, "juru.spec"), encoding="utf-8").read()
    assert "packaging" in spec and "juru_entry.py" in spec
    assert "templates" in spec                       # templates frozen in
    assert '"juru"' in spec
    entry = open(os.path.join(HERE, "packaging", "juru_entry.py"),
                 encoding="utf-8").read()
    assert "from juru.cli import main" in entry
    cli = open(os.path.join(HERE, "src", "juru", "cli.py"), encoding="utf-8").read()
    assert "_MEIPASS" in cli                         # frozen template lookup
    install = open(os.path.join(HERE, "packaging", "INSTALL.txt"),
                   encoding="utf-8").read()
    assert "juru --version" in install and "PATH" in install


def t_batch5_release_pipeline():
    """The release workflow builds 3 interpreters + the extension."""
    wf = open(os.path.join(HERE, ".github", "workflows", "release.yml"),
              encoding="utf-8").read()
    for os_name in ("windows-latest", "ubuntu-latest", "macos-latest"):
        assert os_name in wf, os_name
    assert "Smoke-test the interpreter" in wf    # a broken binary fails loudly
    assert "gh release upload" in wf
    assert "download-artifact" in wf
    assert "vsce package" in wf                 # the .vsix is built too


def t_batch5_extension_runs_code():
    """The extension is a real run button, not just colors."""
    with open(os.path.join(HERE, "vscode", "juru-vscode", "package.json"),
              encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg["main"] == "./extension.js"
    commands = [c["command"] for c in pkg["contributes"]["commands"]]
    assert "juru.runFile" in commands and "juru.openRepl" in commands
    assert "juru.interpreterPath" in pkg["contributes"]["configuration"]["properties"]
    menus = pkg["contributes"]["menus"]["editor/title"]
    assert any(m["command"] == "juru.runFile" and m["when"] == "resourceLangId == juru"
               for m in menus)
    js = open(os.path.join(HERE, "vscode", "juru-vscode", "extension.js"),
              encoding="utf-8").read()
    assert 'registerCommand("juru.runFile"' in js
    assert 'registerCommand("juru.openRepl"' in js
    assert "interpreterAvailable" in js         # friendly missing-interpreter dialog
    guide = open(os.path.join(HERE, "docs", "vscode.md"), encoding="utf-8").read()
    assert "JuRu: Run File" in guide            # the docs teach the button
    assert os.path.exists(os.path.join(HERE, "docs", "install.md"))


# ================================================================ batch 6: the Python-grade setup — REPL parity, icons, one step
def t_batch6_repl_matches_python():
    """The banner and prompt read like Python's, and terminal wishes
    (juru --version, pip, --version, dir) get a nudge, never an error."""
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py")],
        input="juru --version\npip\n--version\ndir\nexit\n",
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out = proc.stdout
    lines = out.splitlines()
    assert lines[0] == "JuRu {} (easy like Python, secure like Rust) on {}".format(
        VERSION, sys.platform), lines[:2]
    assert 'Type "help", "exit" or "cancel" for more information.' in out, out
    assert "juru> " in out and "jruru" not in out, out          # one name only
    assert "not the terminal" in out, out                       # the nudge
    assert "JuRu needs no pip" in out, out                      # pip's own line
    assert "'juru' was not found" not in out, out                # never again
    assert "'pip' was not found" not in out, out
    assert "'version' was not found" not in out, out


def t_batch6_repl_keeps_real_code():
    """`juru = 5` and `juru + 3` are JuRu code, not terminal wishes."""
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "juru.py")],
        input="juru = 5\njuru + 3\nexit\n",
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "=> 8" in proc.stdout, proc.stdout
    assert "not the terminal" not in proc.stdout, proc.stdout


def t_batch6_icons_shipped():
    """The interpreter and the extension carry the real JuRu icon."""
    ico = open(os.path.join(HERE, "logo", "juru_icon.ico"), "rb").read()
    assert ico[:4] == b"\x00\x00\x01\x00" and len(ico) > 10000   # a real .ico
    png = open(os.path.join(HERE, "vscode", "juru-vscode", "images", "juru.png"),
               "rb").read()
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 5000
    spec = open(os.path.join(HERE, "juru.spec"), encoding="utf-8").read()
    assert "juru_icon.ico" in spec                              # the exe wears it
    with open(os.path.join(HERE, "vscode", "juru-vscode", "package.json"),
              encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg["icon"] == "images/juru.png"                     # the extension too


def t_batch6_one_step_setup():
    """setup.bat / install.sh install everything in one step, like a
    real installer: PATH + .jr file icon + interpreter in place."""
    bat = open(os.path.join(HERE, "packaging", "setup.bat"),
               encoding="utf-8").read()
    assert "LOCALAPPDATA" in bat and "reg add" in bat           # install + register
    assert ".jr" in bat and "DefaultIcon" in bat                 # the file icon
    assert "Path" in bat                                         # the PATH update
    sh = open(os.path.join(HERE, "packaging", "install.sh"),
              encoding="utf-8").read()
    assert "/usr/local/bin" in sh and ".local/bin" in sh
    wf = open(os.path.join(HERE, ".github", "workflows", "release.yml"),
              encoding="utf-8").read()
    assert "setup.bat" in wf and "install.sh" in wf              # they ship in the zips
    install = open(os.path.join(HERE, "packaging", "INSTALL.txt"),
                   encoding="utf-8").read()
    assert "setup.bat" in install and "install.sh" in install


def t_batch6_extension_zero_config():
    """The extension finds the interpreter by itself — no settings."""
    with open(os.path.join(HERE, "vscode", "juru-vscode", "package.json"),
              encoding="utf-8") as f:
        pkg = json.load(f)
    prop = pkg["contributes"]["configuration"]["properties"]["juru.interpreterPath"]
    assert prop["default"] == "auto"
    assert any(kb["command"] == "juru.runFile" for kb in pkg["contributes"]["keybindings"])
    assert any(m["command"] == "juru.runFile"
               for m in pkg["contributes"]["menus"].get("explorer/context", []))
    js = open(os.path.join(HERE, "vscode", "juru-vscode", "extension.js"),
              encoding="utf-8").read()
    assert "findInterpreter" in js
    assert "Programs" in js                                      # setup.bat's location
    assert "local/bin" in js                                     # install.sh's locations


# ================================================================ batch 7: the .jr icon in VS Code's explorer + a tidy repo
def t_batch7_language_icon():
    """VS Code shows the JuRu icon next to .jr files (the language
    default icon) — the same slot Python's .py icon gets."""
    with open(os.path.join(HERE, "vscode", "juru-vscode", "package.json"),
              encoding="utf-8") as f:
        pkg = json.load(f)
    lang = pkg["contributes"]["languages"][0]
    assert lang["id"] == "juru"
    icon = lang["icon"]
    assert icon["light"] == icon["dark"] == "./images/juru-file-icon.png"
    png = open(os.path.join(HERE, "vscode", "juru-vscode", "images",
                            "juru-file-icon.png"), "rb").read()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">I", png[16:20])[0] == 32      # small-size icon, crisp
    guide = open(os.path.join(HERE, "docs", "vscode.md"), encoding="utf-8").read()
    assert "file icon" in guide                          # documented


def t_batch7_repo_tidy():
    """The repo stays clean on GitHub: only deliberate files, no junk."""
    git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                         cwd=HERE, capture_output=True, text=True)
    if git.returncode != 0:
        return                                           # not a clone — nothing to enforce
    tracked = subprocess.run(["git", "ls-files"], cwd=HERE,
                             capture_output=True, text=True).stdout.splitlines()
    top = sorted({p.split("/")[0] for p in tracked})
    assert "pr.txt" not in top                           # never part of the repo
    for junk in ("build", "dist", "__pycache__", "src/juru.egg-info", ".vscode"):
        assert not any(p == junk or p.startswith(junk + "/") for p in tracked), junk
    assert not any(p.endswith(".pyc") for p in tracked)
    expected = sorted([
        ".github", ".gitignore", "CHANGELOG.md", "LICENSE", "README.md",
        "checker.py", "design.md", "docs", "examples", "juru.py", "juru.spec",
        "logo", "packaging", "PROGRESS.md", "pyproject.toml", "repl.py",
        "ROADMAP.md", "src", "vscode",
    ] + ["test_%s.py" % s for s in ("checker", "interpreter", "lexer", "mega",
         "packaging", "parser", "programs", "repl", "stdlib", "step12",
         "step15", "step16", "step17", "step22", "step6", "step7", "step8",
         "step9", "templates", "tutorial", "ultimate")])
    assert top == expected, (top, "unexpected or missing top-level files")


# ================================================================ batch 8: the beginner guide — every keyword, one lesson each
GUIDE = os.path.join(HERE, "examples", "guide")

LESSON_KEYWORDS = {
    "00_start_here.jr": ["say"],
    "01_say.jr": ["say"],
    "02_if_else.jr": ["if", "else"],
    "03_while.jr": ["while"],
    "04_counting.jr": ["for", "from", "to"],
    "05_for_in.jr": ["for", "in"],
    "06_break.jr": ["break"],
    "07_continue.jr": ["continue"],
    "08_func.jr": ["func"],
    "09_return.jr": ["return"],
    "10_booleans.jr": ["true", "false", "null"],
    "11_logic.jr": ["and", "or", "not"],
    "12_membership.jr": ["in", "not"],
    "13_import.jr": ["import"],
}


def lesson_code(name):
    """The lesson's code with comment lines removed — comments teach,
    but they do not count as keyword usage."""
    src = open(os.path.join(GUIDE, name), encoding="utf-8").read()
    return "\n".join(line.split("#")[0] for line in src.splitlines())


def t_batch8_guide_exists():
    """The guide folder holds the ramp, 14 numbered lessons and the
    module for lesson 13 — 15 files, properly named."""
    names = sorted(os.listdir(GUIDE))
    expected = sorted(list(LESSON_KEYWORDS) + ["tools.jr"])
    assert names == expected, (names, "unexpected or missing guide files")
    readme = open(os.path.join(HERE, "examples", "README.md"),
                  encoding="utf-8").read()
    assert "Beginner Guide" in readme
    # the old demos moved into examples/test/ — nothing lost
    testdir = sorted(os.listdir(os.path.join(HERE, "examples", "test")))
    assert len([n for n in testdir if n.endswith(".jr")]) == 15
    assert "demo.jr" in testdir and "helpers.jr" in testdir


def t_batch8_every_keyword_taught():
    """Every one of the 19 keywords is genuinely used in the lesson
    that teaches it — in real code, not in comments."""
    from juru.lexer import KEYWORDS
    covered = set()
    for name, kws in LESSON_KEYWORDS.items():
        code = lesson_code(name)
        for kw in kws:
            assert re.search(r"\b{}\b".format(kw), code), \
                "{} never uses its own keyword {}".format(name, kw)
            covered.add(kw)
    assert covered == set(KEYWORDS), sorted(set(KEYWORDS) - covered)
    # lessons are deterministic: no randomness, no questions to the user
    for name in LESSON_KEYWORDS:
        code = lesson_code(name)
        assert "random(" not in code and "ask(" not in code, name


def t_batch8_lessons_run():
    """Every lesson file runs through the real CLI: exit 0, output,
    no traceback. tools.jr (a module) prints nothing by design."""
    for name in sorted(LESSON_KEYWORDS) + ["tools.jr"]:
        proc = subprocess.run(
            [sys.executable, "juru.py", os.path.join("examples", "guide", name)],
            cwd=HERE, capture_output=True, text=True, timeout=120,
        )
        assert proc.returncode == 0, (name, proc.stderr)
        assert "Traceback" not in proc.stderr, (name, proc.stderr)
        if name != "tools.jr":
            assert proc.stdout.strip(), name + " printed nothing"


def t_batch8_guide_doc_links():
    """The guide doc walks every lesson, and both READMEs link them."""
    doc = open(os.path.join(HERE, "examples", "README.md"),
               encoding="utf-8").read()
    for name in LESSON_KEYWORDS:
        assert name in doc, name + " missing from the guide doc"
        assert "guide/" + name in doc, name + " not linked in the guide doc"
    assert "test/demo.jr" in doc          # demos linked too
    readme = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    assert "examples/guide/00_start_here.jr" in readme
    assert "examples/README.md" in readme
    assert "examples/test/demo.jr" in readme


# ================================================================ runner
ALL = [
    ("ALL 19 keywords + dict + import in one program", t_all_19_keywords_one_program),
    ("FINAL BOSS: combined steps 1–7 program", t_final_boss_program),
    ("batch-1 boss: steps 1–9 leaderboard program", t_final_boss_batch1),
    ("word frequency (dict torture)", t_word_frequency_torture),
    ("memoized fibo(25) + fact(15)", t_memoized_fibo),
    ("downward for + dict trap combo", t_dict_trap_combo),
    ("truthiness matrix", t_truthiness_matrix),
    ("type matrix (display/len/in/index/==)", t_type_matrix),
    ("for-in stress: 10000 iterations", t_for_in_stress_10000),
    ("prime sieve (lists + while)", t_prime_sieve),
    ("slice + string pipeline", t_slice_string_pipeline),
    ("random dice torture (seeded)", t_random_dice_torture),
    ("dungeon game sim (seeded)", t_dungeon_game_seeded),
    ("module chain a→b→c runs once", t_module_chain_runs_once),
    ("module readonly + member errors", t_module_readonly_and_errors),
    ("error gauntlet (steps 4–7 messages)", t_error_gauntlet),
    ("checker kills before runtime", t_checker_before_runtime),
    ("reserved audit: all 47 builtins", t_reserved_audit),
    ("mirror rule: all 47 builtins", t_mirror_rule_full),
    ("did-you-mean gauntlet (every surface)", t_did_you_mean_gauntlet),
    ("typo storm over 40 near-identical funcs", t_typo_top_of_recursion_hell),
    ("step 9 pipeline: top words ranked", t_top_words_pipeline),
    ("step 9 guard wall (8 wrong values)", t_step9_guard_wall),
    ("step 9 purity: nothing mutates", t_step9_purity_never_mutates),
    ("all 15 demo programs via the real CLI", t_all_15_examples_via_cli),
    ("checker approves all 15 examples", t_checker_approves_all_examples),
    ("REPL torture: dicts + import + recovery", t_repl_dict_import_torture),
    ("REPL multi-line session (blocks + recovery)", t_repl_multiline_session),
    ("REPL: the 6 new tools live", t_repl_new_builtins_live),
    ("batch 4: version 1.9, 47 builtins, 19 keywords", t_batch4_version_bump),
    ("batch 2: --new quiz end-to-end via CLI", t_templates_end_to_end),
    ("batch 2: --new refusal gauntlet", t_new_refusal_gauntlet),
    ("batch 2: --templates listing complete", t_templates_listing_complete),
    ("batch 2: tutorial graduation program", t_tutorial_graduation_program),
    ("batch 3: wave-3 builtins live", t_batch3_wave3_builtins_live),
    ("batch 3: repl subcommand", t_batch3_repl_subcommand),
    ("batch 3: calculator speaks decimals", t_batch3_calculator_float_session),
    ("batch 3: package + editor sanity", t_batch3_package_and_editor),
    ("batch 4: help + sleep live", t_batch4_help_and_sleep_live),
    ("batch 4: help database is truthful", t_batch4_helpdb_is_truthful),
    ("batch 4: caret errors via the CLI", t_batch4_caret_errors_via_cli),
    ("batch 4: bare command opens the REPL", t_batch4_bare_command_is_repl),
    ("batch 5: frozen build files agree", t_batch5_frozen_build_files),
    ("batch 5: release pipeline builds 4 downloads", t_batch5_release_pipeline),
    ("batch 5: the extension runs code", t_batch5_extension_runs_code),
    ("batch 6: the REPL reads like Python's", t_batch6_repl_matches_python),
    ("batch 6: real JuRu code stays code", t_batch6_repl_keeps_real_code),
    ("batch 6: the icons are real", t_batch6_icons_shipped),
    ("batch 6: one-step setup files", t_batch6_one_step_setup),
    ("batch 6: the extension needs zero config", t_batch6_extension_zero_config),
    ("batch 7: the .jr icon lives in VS Code's explorer", t_batch7_language_icon),
    ("batch 7: the repo stays tidy on GitHub", t_batch7_repo_tidy),
    ("batch 8: the guide folder is complete", t_batch8_guide_exists),
    ("batch 8: every keyword has its lesson", t_batch8_every_keyword_taught),
    ("batch 8: every lesson runs", t_batch8_lessons_run),
    ("batch 8: the guide doc links everything", t_batch8_guide_doc_links),
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
