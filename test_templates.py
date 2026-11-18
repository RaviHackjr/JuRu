"""JuRu Step 10 tests — templates: start a real program in one command.

The templates are beginner programs with exact, verified behaviour:
  starter.jr        no input, deterministic output
  calculator.jr     interactive, guarded (bad math, bad input, exit)
  quiz.jr           interactive, deterministic questions
  guessing_game.jr  interactive, always ends in at most 7 guesses
  word_stats.jr     no input, deterministic output

Every template must run through the real CLI, and --new must copy them
politely (never overwrite, friendly refusals).
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.checker import check_source
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


def cli(args, cwd=HERE, input_text=None):
    return subprocess.run(
        [sys.executable, JURU] + args,
        input=input_text, capture_output=True, text=True, cwd=cwd, timeout=120,
    )


def in_sandbox():
    """A fresh temp dir so --new files never touch the project."""
    return tempfile.mkdtemp(prefix="juru_new_")


def template_names():
    return sorted(
        name[:-3] for name in os.listdir(os.path.join(HERE, "src", "juru", "templates"))
        if name.endswith(".jr")
    )


EXPECTED_STARTER = """hello, friend!
level 3, progress 7.5
step 1
step 2
step 3
you carry 4 items
[shield, potion]
"""

EXPECTED_WORD_STATS = """total words: 9
and appears 1 time(s)
cat appears 2 time(s)
dog appears 1 time(s)
ran appears 1 time(s)
saw appears 1 time(s)
the appears 3 time(s)
'the' first sits at index 0
no 'zebra' in there: true
"""

EXPECTED_CALCULATOR = """tiny calculator — type like 5 + 3 or 2.5 * 2, or exit
> = 8
> = 5.0
> = 2.5
> = 81
> cannot divide by zero
> I know + - * / only
> I need three parts, like 5 + 3
> bye!
"""

EXPECTED_QUIZ = """What is 2 + 2?
your answer: correct!
Capital of France?
your answer: correct!
JuRu files end with...?
your answer: correct!
score: 3/3
perfect!
"""


# ------------------------------------------------------------------ templates exist
def t_five_templates_exist():
    assert template_names() == [
        "calculator", "guessing_game", "quiz", "starter", "word_stats",
    ], template_names()


def t_every_template_is_valid():
    for name in template_names():
        path = os.path.join(HERE, "src", "juru", "templates", name + ".jr")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        check_source(src)           # raises on any semantic mistake


def t_templates_listing():
    proc = cli(["--templates"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for name in template_names():
        assert name in proc.stdout, name
    assert "--new NAME TEMPLATE" in proc.stdout, proc.stdout


# ------------------------------------------------------------------ deterministic templates
def t_starter_exact():
    proc = cli([os.path.join("src", "juru", "templates", "starter.jr")])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == EXPECTED_STARTER, proc.stdout


def t_word_stats_exact():
    proc = cli([os.path.join("src", "juru", "templates", "word_stats.jr")])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == EXPECTED_WORD_STATS, proc.stdout


# ------------------------------------------------------------------ interactive templates
def t_calculator_session():
    proc = cli([os.path.join("src", "juru", "templates", "calculator.jr")],
               input_text="5 + 3\n2.5 * 2\n10 / 4\n9 * 9\n7 / 0\n5 x 2\nabc\nexit\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == EXPECTED_CALCULATOR, proc.stdout


def t_calculator_eof_is_friendly():
    """Input ends mid-session — never 'a bug, not your fault'."""
    proc = cli([os.path.join("src", "juru", "templates", "calculator.jr")], input_text="5 + 3\n")
    assert proc.returncode == 1
    assert "ask() could not read any more input" in proc.stdout, proc.stdout
    assert "not your fault" not in proc.stdout, proc.stdout


def t_quiz_session():
    proc = cli([os.path.join("src", "juru", "templates", "quiz.jr")],
               input_text="4\nParis\n.jr\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == EXPECTED_QUIZ, proc.stdout


def t_quiz_wrong_answers():
    proc = cli([os.path.join("src", "juru", "templates", "quiz.jr")],
               input_text="5\nBerlin\npy\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "nope — it was 4" in proc.stdout
    assert "score: 0/3" in proc.stdout
    assert "try again for a perfect run" in proc.stdout


def t_guessing_game_always_ends():
    """Seven honest guesses of 50: the game must end either way."""
    proc = cli([os.path.join("src", "juru", "templates", "guessing_game.jr")],
               input_text="50\n" * 7)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "guess 7: " in proc.stdout, proc.stdout
    assert ("got it in " in proc.stdout) or ("out of tries — it was " in proc.stdout), proc.stdout
    assert "higher" in proc.stdout or "lower" in proc.stdout, proc.stdout


def t_guessing_game_shape_is_sound():
    """Whatever the secret: rounds are prompts with a hint riding along
    ('guess 3: lower'), and the game ends with exactly ONE win/reveal line
    whose round number matches the rounds actually played."""
    proc = cli([os.path.join("src", "juru", "templates", "guessing_game.jr")],
               input_text="50\n25\n75\n12\n88\n6\n94\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if ln]
    last = lines[-1]
    assert "got it in" in last or "out of tries" in last, lines
    for ln in lines[:-1]:
        assert "guess " in ln and ("higher" in ln or "lower" in ln), lines
    if "got it in" in last:
        round_no = int(last.split("guess ")[1].split(":")[0])
        tries_no = int(last.split("in ")[1].split(" ")[0])
        assert round_no == tries_no == len(lines), (last, lines)
    else:
        assert len(lines) == 8, lines      # 7 hint rounds + the reveal
        assert "it was " in last, last


# ------------------------------------------------------------------ --new
def t_new_default_is_starter():
    d = in_sandbox()
    proc = cli(["--new", "hello"], cwd=d)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    with open(os.path.join(d, "hello.jr"), encoding="utf-8") as f:
        made = f.read()
    with open(os.path.join(HERE, "src", "juru", "templates", "starter.jr"), encoding="utf-8") as f:
        original = f.read()
    assert made == original, "the copy must be exact"
    assert "created hello.jr from the 'starter' template" in proc.stdout
    assert "run it:  python3 juru.py hello.jr" in proc.stdout
    run = cli([os.path.join(d, "hello.jr")])
    assert run.returncode == 0 and run.stdout == EXPECTED_STARTER, run.stdout


def t_new_chosen_template():
    d = in_sandbox()
    proc = cli(["--new", "myquiz", "quiz"], cwd=d)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert os.path.exists(os.path.join(d, "myquiz.jr"))
    assert "created myquiz.jr from the 'quiz' template" in proc.stdout


def t_new_never_overwrites():
    d = in_sandbox()
    cli(["--new", "keep"], cwd=d)
    before = open(os.path.join(d, "keep.jr"), encoding="utf-8").read()
    proc = cli(["--new", "keep", "quiz"], cwd=d)
    assert proc.returncode == 1, proc.stdout
    assert "'keep.jr' already exists — pick another name (I never overwrite)" in proc.stdout
    after = open(os.path.join(d, "keep.jr"), encoding="utf-8").read()
    assert before == after, "the file must not be touched"


def t_new_rejects_bad_names():
    d = in_sandbox()
    for bad in ["bad name", "", "1abc", "-x", "../escape", "a/b"]:
        proc = cli(["--new", bad], cwd=d)
        assert proc.returncode == 1, "accepted bad name: " + repr(bad)
        assert "not a usable program name" in proc.stdout, proc.stdout
    assert os.listdir(d) == [], "nothing may be created for bad names"


def t_new_unknown_template_suggests():
    d = in_sandbox()
    proc = cli(["--new", "x", "qiz"], cwd=d)
    assert proc.returncode == 1, proc.stdout
    assert "no template 'qiz' — did you mean 'quiz'?" in proc.stdout, proc.stdout
    assert "starter" in proc.stdout, proc.stdout
    proc = cli(["--new", "x", "zzzzzz"], cwd=d)
    assert proc.returncode == 1, proc.stdout
    assert "the templates are:" in proc.stdout, proc.stdout


def t_new_missing_name():
    proc = cli(["--new"])
    assert proc.returncode == 1, proc.stdout
    assert "--new NAME" in proc.stdout, proc.stdout


def t_new_starter_without_template_arg():
    d = in_sandbox()
    proc = cli(["--new", "solo"], cwd=d)
    assert proc.returncode == 0 and os.path.exists(os.path.join(d, "solo.jr"))


# ------------------------------------------------------------------ CLI housekeeping
def t_version_flag():
    proc = cli(["--version"])
    assert proc.returncode == 0 and proc.stdout == "JuRu {}\n".format(VERSION), proc.stdout


def t_help_flag():
    for flag in ("--help", "-h"):
        proc = cli([flag])
        assert proc.returncode == 0, proc.stdout
        assert "--new NAME" in proc.stdout and program_line() in proc.stdout, proc.stdout


def program_line():
    return "python3 juru.py program.jr"


def t_unknown_flag_is_friendly():
    proc = cli(["--wat"])
    assert proc.returncode == 1, proc.stdout
    assert "I do not know '--wat' — try python3 juru.py --help" in proc.stdout


def t_no_args_opens_repl():
    """No arguments opens the REPL — exactly like bare `python`."""
    proc = cli([], input_text="say(7 * 6)\nexit\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "JuRu {} (easy like Python".format(VERSION) in proc.stdout, proc.stdout
    assert "juru> 42" in proc.stdout, proc.stdout


def t_templates_manifest_in_sync():
    """The manifest in juru.py and the files in templates/ must agree."""
    from juru import cli as cli_module
    assert sorted(cli_module.TEMPLATES) == template_names(), cli_module.TEMPLATES


def t_language_untouched_by_batch2():
    """Templates added zero language surface; later batches added exactly
    6 builtins (float, pow, pop, type, help, sleep) and zero keywords;
    Step 22 added 17 collection builtins, still zero keywords;
    Step 23 added try/rescue + fail:
    21 keywords, 48 builtins."""
    from juru.lexer import KEYWORDS
    from juru.checker import BUILTINS
    assert len(KEYWORDS) == 21     # try/rescue (Step 23) + fail builtin
    assert len(BUILTINS) == 48
    for name in ("float", "pow", "pop", "type", "help", "sleep",
                 "insert", "remove_at", "unique", "set_of", "union"):
        assert name in BUILTINS


ALL = [
    ("5 templates exist", t_five_templates_exist),
    ("every template is semantically valid", t_every_template_is_valid),
    ("--templates lists them all", t_templates_listing),
    ("starter: exact output", t_starter_exact),
    ("word_stats: exact output", t_word_stats_exact),
    ("calculator: guarded session", t_calculator_session),
    ("calculator: EOF is friendly", t_calculator_eof_is_friendly),
    ("quiz: perfect run", t_quiz_session),
    ("quiz: wrong answers", t_quiz_wrong_answers),
    ("guessing_game: always ends", t_guessing_game_always_ends),
    ("guessing_game: output shape is sound", t_guessing_game_shape_is_sound),
    ("--new: default starter copy", t_new_default_is_starter),
    ("--new: chosen template", t_new_chosen_template),
    ("--new: never overwrites", t_new_never_overwrites),
    ("--new: rejects bad names", t_new_rejects_bad_names),
    ("--new: unknown template suggests", t_new_unknown_template_suggests),
    ("--new: missing name", t_new_missing_name),
    ("--new: starter without template arg", t_new_starter_without_template_arg),
    ("--version", t_version_flag),
    ("--help / -h", t_help_flag),
    ("unknown flag is friendly", t_unknown_flag_is_friendly),
    ("no args opens the REPL", t_no_args_opens_repl),
    ("manifest in sync with files", t_templates_manifest_in_sync),
    ("batch 2 added zero language surface", t_language_untouched_by_batch2),
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
