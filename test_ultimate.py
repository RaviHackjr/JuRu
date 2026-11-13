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
import os
import random as pyrandom
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import JuRuGalti, KEYWORDS
from parser import parse_source
from checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
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
        'import "examples/helpers.jr"\n'
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
    src = 'import "examples/helpers.jr"\nsay(helpers)\n'
    assert run(src, base_dir=HERE) == "<module helpers>\n"
    expect_galti('import "examples/helpers.jr"\nsay(helpers.nope)',
                 "'helpers' has no 'nope' — the module has: double, greet, magic",
                 base_dir=HERE)
    expect_check_galti('import "examples/helpers.jr"\nhelpers.magic = 5',
                       "'data.key = value' does not work")


def t_error_gauntlet():
    """Every big error message of steps 4–7, exact fragments, in one go."""
    expect_galti('d = {"a": 1}\nsay(d["z"])',
                 "key 'z' was not found — this dict has: a")
    expect_galti("say([1, 2, 3][1:99][-5:2])",
                 "the slice start cannot be negative")
    expect_galti('split("a", "")', "the split separator cannot be empty")
    expect_galti('replace("a", "", "b")', "the old text cannot be empty in replace()")
    expect_galti("sqrt(-1)", "sqrt(-1) — a negative number has no square root")
    expect_galti('say({"a": 1}[1.5])', "a dict key must be text or a whole number — got: 1.5")
    expect_galti('for x in 5 { say(x) }',
                 "'for x in ...' needs a list, text, or dict — got: 5")
    expect_galti('say(5 in 5)', "'in' needs a list, text, or dict on the right — got: 5")
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
def t_reserved_audit_24():
    assert len(BUILTINS) == 24
    wave1 = {"split", "join", "trim", "replace", "abs", "round", "random", "sqrt"}
    wave2 = {"sorted", "reverse", "find", "keys", "values", "count"}
    assert wave1 <= set(BUILTINS)
    assert wave2 <= set(BUILTINS)
    for name in BUILTINS:
        expect_check_galti("{} = 1".format(name),
                           "'{}' is reserved (builtin) — pick another name".format(name))
        expect_check_galti(
            "func {}(a) {{\n    return a\n}}".format(name),
            "'{}' is reserved (builtin) — pick another name".format(name))
    assert len(KEYWORDS) == 19          # steps 8–9 added zero keywords
    assert {"in", "import"} <= set(KEYWORDS)


def t_mirror_rule_full_24():
    """Wrong arity: checker message == runtime message == hint, for all 24."""
    for name, (lo, hi) in BUILTIN_ARITY.items():
        hint = BUILTIN_HINT[name]
        calls = []
        if lo > 0:                      # too few (ask() alone is legal: (0, 1))
            inner = ", ".join(["1"] * (lo - 1))
            calls.append("{}({})".format(name, inner))
        calls.append("{}({})".format(name, ", ".join(["1"] * (hi + 1))))   # too many
        for call in calls:
            expect_check_galti(call, hint)
            expect_galti(call, hint)


def t_all_15_examples_via_cli():
    names = sorted(os.listdir(os.path.join(HERE, "examples")))
    assert len(names) == 15, "expected 15 examples, got: " + str(names)
    for name in names:
        if not name.endswith(".jr"):
            continue
        proc = subprocess.run(
            [sys.executable, "juru.py", os.path.join("examples", name)],
            capture_output=True, text=True, cwd=HERE, timeout=60,
        )
        assert proc.returncode == 0, "{} failed:\n{}{}".format(
            name, proc.stdout, proc.stderr)


def t_checker_approves_all_examples():
    for name in sorted(os.listdir(os.path.join(HERE, "examples"))):
        if not name.endswith(".jr"):
            continue
        with open(os.path.join(HERE, "examples", name), encoding="utf-8") as f:
            src = f.read()
        check_source(src)               # raises on any semantic mistake


def t_repl_dict_import_torture():
    out = run_repl([
        'import "examples/helpers.jr"',
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
        ln = ln.replace("......> ", "").replace("jruru> ", "")
        if ln in ("jruru>", "......>"):
            ln = ""
        if ln:
            clean.append(ln)
    text = "\n".join(clean)
    assert clean[0].startswith("JuRu 1.2 REPL"), out
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
        run('import "examples/helpers.jr"\nsay(helpers.duble(2))')
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
        'import "examples/helpers.jr"\n'
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
    """A real session: blocks across lines, ......> prompts, echoes, recovery."""
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
        ln = ln.replace("......> ", "").replace("jruru> ", "")
        if ln in ("jruru>", "......>"):
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
    assert "......>" in out                 # the continuation prompt was shown


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
        ln = ln.replace("......> ", "").replace("jruru> ", "")
        if ln in ("jruru>", "......>"):
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
    ("reserved audit: all 24 builtins", t_reserved_audit_24),
    ("mirror rule: all 24 builtins", t_mirror_rule_full_24),
    ("did-you-mean gauntlet (every surface)", t_did_you_mean_gauntlet),
    ("typo storm over 40 near-identical funcs", t_typo_top_of_recursion_hell),
    ("step 9 pipeline: top words ranked", t_top_words_pipeline),
    ("step 9 guard wall (8 wrong values)", t_step9_guard_wall),
    ("step 9 purity: nothing mutates", t_step9_purity_never_mutates),
    ("all 15 examples via the real CLI", t_all_15_examples_via_cli),
    ("checker approves all 15 examples", t_checker_approves_all_examples),
    ("REPL torture: dicts + import + recovery", t_repl_dict_import_torture),
    ("REPL multi-line session (blocks + recovery)", t_repl_multiline_session),
    ("REPL: the 6 new tools live", t_repl_new_builtins_live),
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
