"""JuRu Step 11 tests — the tutorial cannot lie.

docs/tutorial.md is executable documentation. Rules enforced here:
  - every ```jr block is semantically valid (the checker must approve it)
  - a ```jr block followed by a plain block must print EXACTLY that output
  - if the expected output starts with "JuRu Error", the block must fail
    with exactly that message (line/col included)
  - a ```jr block with NO output block must print NOTHING
  - a ```jr block containing ask() is interactive: checker-only, and it
    must NOT be paired with an output block
  - the tutorial must mention all 21 keywords, all 48 builtins and every
    example file (docs stay in sync with the language)
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.checker import check_source, BUILTINS
from juru.interpreter import Interpreter
from juru.version import VERSION

HERE = os.path.dirname(os.path.abspath(__file__))
TUTORIAL = os.path.join(HERE, "docs", "tutorial.md")
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


def parse_blocks(text):
    """Markdown fences, in order: [(lang, body), ...] — ```x opens, ``` closes."""
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            blocks.append((lang, "\n".join(body)))
        i += 1
    return blocks


def run_block(src):
    """checker → interpreter → stdout (raises JuRuGalti when the program does)."""
    tree = check_source(src)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=HERE)
    return buf.getvalue()


def blocks():
    with open(TUTORIAL, encoding="utf-8") as f:
        return parse_blocks(f.read())


def tutorial_text():
    with open(TUTORIAL, encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------------ structure
def t_every_jr_block_is_valid():
    """Every ```jr block must pass the checker — except the deliberate
    error demos, which are allowed to fail ONLY when the paired output
    documents exactly that JuRu error."""
    count = 0
    bs = blocks()
    for i, (lang, body) in enumerate(bs):
        if lang != "jr":
            continue
        nxt = bs[i + 1] if i + 1 < len(bs) else (None, None)
        documented_error = nxt[0] == "" and nxt[1].strip().startswith("JuRu Error")
        try:
            check_source(body)
        except JuRuGalti:
            assert documented_error, "an undokumented error in a ```jr block:\n" + body
        count += 1
    assert count >= 25, "tutorial shrank? only {} jr blocks".format(count)


def t_output_pairs_are_exact():
    """Each ```jr block followed by a plain block: exact stdout (or exact
    JuRu error when the expected text starts with 'JuRu Error')."""
    checked = 0
    bs = blocks()
    for i, (lang, body) in enumerate(bs):
        if lang != "jr":
            continue
        nxt = bs[i + 1] if i + 1 < len(bs) else (None, None)
        if nxt[0] != "":                # no output pair — checked separately
            continue
        expected = nxt[1].strip("\n")
        if "ask(" in body:
            raise AssertionError(
                "an ask() block must not claim output (block near: {}...)"
                .format(body[:40]))
        if expected.startswith("JuRu Error"):
            try:
                run_block(body)
            except JuRuGalti as err:
                assert str(err) == expected, "expected:\n{}\ngot:\n{}".format(
                    expected, str(err))
            else:
                raise AssertionError("expected an error:\n" + expected)
        else:
            out = run_block(body)
            assert out.strip("\n") == expected, "expected:\n{}\ngot:\n{}".format(
                expected, out.strip("\n"))
        checked += 1
    assert checked >= 18, "too few verified output pairs: {}".format(checked)


def t_plain_blocks_print_nothing():
    """A ```jr block with no output pair must be silent (anything it prints
    must be documented — that is the whole deal). Empty is fine: it just
    means every printing block currently documents its output."""
    bs = blocks()
    for i, (lang, body) in enumerate(bs):
        if lang != "jr" or "ask(" in body:
            continue
        nxt = bs[i + 1] if i + 1 < len(bs) else (None, None)
        if nxt[0] == "":
            continue
        out = run_block(body)
        assert out == "", "block prints undocumented output:\n{}".format(out)


def t_ask_blocks_are_checker_only():
    """ask() blocks: valid code, never paired with output."""
    count = 0
    bs = blocks()
    for i, (lang, body) in enumerate(bs):
        if lang != "jr":
            continue
        if "ask(" in body:
            check_source(body)
            nxt = bs[i + 1] if i + 1 < len(bs) else (None, None)
            assert nxt[0] != "", "an ask() block must not claim output"
            count += 1
    assert count >= 1, "the tutorial must teach ask()"


def t_no_stray_jr_blocks_unverified():
    """Every ```jr block falls into exactly one verified bucket."""
    bs = blocks()
    paired = silent = interactive = 0
    for i, (lang, body) in enumerate(bs):
        if lang != "jr":
            continue
        nxt = bs[i + 1] if i + 1 < len(bs) else (None, None)
        if nxt[0] == "":
            paired += 1
        elif "ask(" in body:
            interactive += 1
        else:
            silent += 1
    total = sum(1 for lang, _ in bs if lang == "jr")
    assert paired + silent + interactive == total, (paired, silent, interactive, total)


# ------------------------------------------------------------------ completeness
def t_all_keywords_mentioned():
    text = tutorial_text()
    for kw in KEYWORDS:
        assert re.search(r"\b{}\b".format(re.escape(kw)), text), \
            "keyword missing from the tutorial: " + kw


def t_all_builtins_mentioned():
    text = tutorial_text()
    for builtin in BUILTINS:
        assert re.search(r"\b{}\b".format(re.escape(builtin)), text), \
            "builtin missing from the tutorial: " + builtin


def t_all_examples_mentioned():
    text = tutorial_text()
    for folder in ("test", "guide"):
        names = sorted(os.listdir(os.path.join(HERE, "examples", folder)))
        for name in names:
            if not name.endswith(".jr"):
                continue
            assert name in text, "example missing from the tutorial: " + name


def t_all_templates_mentioned():
    text = tutorial_text()
    names = sorted(name[:-3] for name in
                   os.listdir(os.path.join(HERE, "src", "juru", "templates"))
                   if name.endswith(".jr"))
    for name in names:
        assert name in text, "template missing from the tutorial: " + name


def t_version_mentioned():
    assert "JuRu {} (easy like Python".format(VERSION) in tutorial_text()


# ------------------------------------------------------------------ the quickstart flow
def t_quickstart_flow_works():
    """Chapter 2's promise, executed for real: --new hello, then run it."""
    d = tempfile.mkdtemp(prefix="juru_tut_")
    created = subprocess.run(
        [sys.executable, JURU, "--new", "hello"],
        capture_output=True, text=True, cwd=d, timeout=60,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    assert "created hello.jr from the 'starter' template" in created.stdout
    ran = subprocess.run(
        [sys.executable, JURU, os.path.join(d, "hello.jr")],
        capture_output=True, text=True, cwd=HERE, timeout=60,
    )
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert ran.stdout == (
        "hello, friend!\n"
        "level 3, progress 7.5\n"
        "step 1\nstep 2\nstep 3\n"
        "you carry 4 items\n[shield, potion]\n"
    ), ran.stdout


ALL = [
    ("every ```jr block is semantically valid", t_every_jr_block_is_valid),
    ("output pairs are exact", t_output_pairs_are_exact),
    ("unpaired blocks print nothing", t_plain_blocks_print_nothing),
    ("ask() blocks are checker-only", t_ask_blocks_are_checker_only),
    ("every ```jr block falls in a verified bucket", t_no_stray_jr_blocks_unverified),
    ("all 21 keywords mentioned", t_all_keywords_mentioned),
    ("all 48 builtins mentioned", t_all_builtins_mentioned),
    ("all 15 examples mentioned", t_all_examples_mentioned),
    ("all 5 templates mentioned", t_all_templates_mentioned),
    ("version banner current", t_version_mentioned),
    ("chapter 2 quickstart flow works", t_quickstart_flow_works),
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
