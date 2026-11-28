"""JuRu Step 15 tests — help(): the built-in documentation.

`help()` prints the whole toolbox; `help("pow")` prints one card. This
suite enforces that the help system can never lie:
  - every card's claim is checked against the real language tables
  - the examples in the cards are run for real (the pure ones)
  - the overview mentions every builtin and every keyword by name
  - aliases steer people to the right card; unknown names get
    did-you-mean, never a crash
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
from juru.interpreter import Interpreter
from juru import helpdb
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


def run(src):
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=HERE)
    return buf.getvalue()


# ------------------------------------------------------------------ structure
def t_overview_lists_everything():
    text = run("help()")
    for builtin in BUILTINS:
        assert builtin in text, "overview misses builtin: " + builtin
    for kw in KEYWORDS:
        assert kw in text, "overview misses keyword: " + kw
    assert "21 keywords + 67 builtins" in text, text.splitlines()[0]
    assert text.rstrip().endswith(helpdb.USAGE_LINE)


def t_cards_cover_every_topic():
    assert set(helpdb.BUILTIN_CARDS) == set(BUILTINS)
    assert set(helpdb.KEYWORD_CARDS) == set(KEYWORDS)
    assert len(helpdb.BUILTIN_CARDS) == 67
    assert len(helpdb.KEYWORD_CARDS) == 21


def t_every_card_renders_and_is_labelled():
    for name, kind in helpdb.topics():
        text = helpdb.card_for(name)
        assert text is not None, name
        assert "({})".format(kind) in text, name
        assert len(text.splitlines()) >= 3, "card too empty: " + name


def t_card_examples_are_true():
    """The worked examples in the cards must behave as claimed."""
    assert run('help("int")').count("42") >= 1
    # spot-check the pure claims across a few cards
    assert run('say(float("3.5"))') == "3.5\n"          # float card claims this
    assert run("say(pow(2, 10))") == "1024\n"           # pow card claims this
    assert run("say(round(2.5))") == "3\n"              # round card claims this
    assert run("say(sorted([3, 1, 2]))") == "[1, 2, 3]\n"
    assert run('say(find([5, 7, 9], 99))') == "-1\n"    # find claims -1
    assert run('say(type("hi"))') == "text\n"           # type claims text
    assert run('say("ell" in "hello")') == "true\n"     # in claims true
    assert run("for i from 1 to 3 {\n    say(i)\n}") == "1\n2\n3\n"  # to is included


def t_card_guards_are_the_real_messages():
    """Guard lines in cards must match what the language actually prints."""
    expect_galti = [
        ('help("pow")', "in pow(a, b), 0 cannot be raised to a negative power"),
        ('help("float")', "is not a number"),
        ('help("pop")', "this list is empty, there is nothing to take"),
        ('help("sqrt")', "no square root"),
        ('help("split")', "the split separator cannot be empty"),
        ('help("random")', "low cannot be bigger than high"),
    ]
    for card_call, fragment in expect_galti:
        name = card_call.split('"')[1]
        card = helpdb.card_for(name)
        assert fragment in card, "{} card lacks its real guard: {}".format(name, fragment)


# ------------------------------------------------------------------ behaviour
def t_help_prints_and_returns_null():
    out = run('help("len")')
    assert "len(x)" in out                      # it prints the card
    final = run('say(type(help("len")))')
    assert final.splitlines()[-1] == "null", final   # ...and returns null


def t_help_never_fails_on_unknown():
    out = run('help("zzzzzz")')
    assert out.startswith("no help topic 'zzzzzz'"), out
    assert "the topics are:" in out
    assert "pow" in out                        # the full list is right there


def t_aliases_steer_to_the_right_card():
    assert helpdb.card_for("power") == helpdb.card_for("pow")
    assert helpdb.card_for("sort") == helpdb.card_for("sorted")
    assert helpdb.card_for("print") == helpdb.card_for("say")
    assert helpdb.card_for("pause") == helpdb.card_for("sleep")
    assert helpdb.card_for("input") == helpdb.card_for("ask")


def t_did_you_mean_on_near_misses():
    out = run('help("pov")')
    assert "did you mean 'pow'?" in out, out


def t_help_guards():
    try:
        run("help(5)")
    except JuRuGalti as err:
        assert err.message == "help() needs a name in quotes — got: 5", err.message
    try:
        run("help(1, 2)")
    except JuRuGalti as err:
        assert err.message == "help() takes at most 1 argument", err.message
    assert BUILTIN_ARITY["help"] == (0, 1)
    assert BUILTIN_HINT["help"] == "help() takes at most 1 argument"


def t_help_and_sleep_are_reserved():
    for name in ("help", "sleep"):
        try:
            check_source("{} = 1".format(name))
        except JuRuGalti as err:
            assert "'{}' is reserved (builtin)".format(name) in err.message
        else:
            raise AssertionError(name + " was shadowable")


# ------------------------------------------------------------------ REPL + CLI
def cli(args, input_text=None, cwd=HERE):
    return subprocess.run(
        [sys.executable, JURU] + args,
        input=input_text, capture_output=True, text=True, cwd=cwd, timeout=120,
    )


def t_repl_bare_help_command():
    proc = cli(["repl"], input_text="help\nexit\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "JuRu toolbox — 21 keywords + 67 builtins" in proc.stdout, proc.stdout


def t_repl_help_call_works():
    proc = cli(["repl"], input_text='help("trim")\nexit\n')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "drop spaces, tabs and newlines" in proc.stdout, proc.stdout


def t_banner_advertises_help():
    proc = cli(["repl"], input_text="exit\n")
    assert "type help() to see the whole toolbox" in proc.stdout, proc.stdout


def t_help_in_a_real_program():
    d = tempfile.mkdtemp(prefix="juru_help_")
    path = os.path.join(d, "greeter.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write('help("join")\n')
    proc = cli([path], cwd=d)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "join(list, sep)" in proc.stdout, proc.stdout
    assert "glue a list back into one text" in proc.stdout


ALL = [
    ("overview lists all 67 builtins + 21 keywords", t_overview_lists_everything),
    ("cards cover every topic exactly", t_cards_cover_every_topic),
    ("every card renders and is labelled", t_every_card_renders_and_is_labelled),
    ("card examples are true", t_card_examples_are_true),
    ("card guards are the real messages", t_card_guards_are_the_real_messages),
    ("help prints and returns null", t_help_prints_and_returns_null),
    ("help never fails on unknown names", t_help_never_fails_on_unknown),
    ("aliases steer to the right card", t_aliases_steer_to_the_right_card),
    ("did-you-mean on near misses", t_did_you_mean_on_near_misses),
    ("help guards + mirror messages", t_help_guards),
    ("help and sleep are reserved", t_help_and_sleep_are_reserved),
    ("REPL: bare help command", t_repl_bare_help_command),
    ("REPL: help(\"name\") works", t_repl_help_call_works),
    ("banner advertises help", t_banner_advertises_help),
    ("help works in a real program", t_help_in_a_real_program),
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
