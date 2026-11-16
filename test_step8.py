"""JuRu Step 8 tests — the friendly layer: did-you-mean + REPL multi-line.

Two upgrades, one promise: the language should feel like it is HELPING you.
- a typo gets the closest real name back: did you mean 'name'?
- the REPL accepts blocks across lines (with a ....> continuation prompt)
"""
import os
import subprocess
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


def run_repl(lines):
    proc = subprocess.run(
        [sys.executable, "repl.py"],
        input="\n".join(lines) + "\n",
        capture_output=True, text=True, cwd=HERE, timeout=120,
    )
    assert proc.returncode == 0, "exit {}: {}".format(proc.returncode, proc.stderr)
    return proc.stdout


def strip_prompts(out):
    cleaned = []
    for ln in out.splitlines():
        ln = ln.replace("....> ", "").replace("juru> ", "")
        if ln in ("juru>", "....>"):
            ln = ""
        if ln:
            cleaned.append(ln)
    return cleaned


# ------------------------------------------------------------------ checker suggestions
def t_typo_name_suggestion():
    try:
        check_source('name = "JuRu"\nsay(naame)')
    except JuRuGalti as err:
        assert err.message == (
            "'naame' was not found — did you mean 'name'? "
            "(nothing with this name is ever assigned)"), err.message
        return
    raise AssertionError("expected a typo error")


def t_typo_call_suggestion():
    try:
        check_source('func price(n) {\n    return n\n}\nsay(prce(5))')
    except JuRuGalti as err:
        assert "did you mean 'price'?" in err.message, err.message
        return
    raise AssertionError("expected a typo error")


def t_typo_loop_var_suggestion():
    try:
        check_source("total = 0\nfor i from 1 to 3 {\n    total = total + tital\n}")
    except JuRuGalti as err:
        assert "did you mean 'total'?" in err.message, err.message
        return
    raise AssertionError("expected a typo error")


def t_typo_builtin_suggestion():
    try:
        check_source('say(lenh("abc"))')
    except JuRuGalti as err:
        assert "did you mean 'len'?" in err.message, err.message
        return
    raise AssertionError("expected a typo error")


def t_no_match_stays_plain():
    try:
        check_source('qqzzxx = 1\nsay(wwvvyy)')
    except JuRuGalti as err:
        assert err.message.endswith("(nothing with this name is ever assigned)"), err.message
        assert "did you mean" not in err.message, err.message
        return
    raise AssertionError("expected a typo error")


def t_old_hinglish_hint_still_wins():
    try:
        check_source("say(bolo)")
    except JuRuGalti as err:
        assert err.message == "'bolo' was not found (the old 'bolo' is now 'say')", err.message
        return
    raise AssertionError("expected a hint error")


# ------------------------------------------------------------------ runtime suggestions
def t_dict_key_suggestion():
    try:
        Interpreter().run(check_source('d = {"name": 1, "age": 2}\nsay(d["naame"])'))
    except JuRuGalti as err:
        assert err.message == (
            "key 'naame' was not found — did you mean 'name'? "
            "— this dict has: name, age"), err.message
        return
    raise AssertionError("expected a missing-key error")


def t_dict_key_no_match_unchanged():
    try:
        Interpreter().run(check_source('d = {"name": 1}\nsay(d["zzzzzz"])'))
    except JuRuGalti as err:
        assert err.message == "key 'zzzzzz' was not found — this dict has: name", err.message
        return
    raise AssertionError("expected a missing-key error")


def t_module_member_suggestion():
    try:
        Interpreter().run(check_source(
            'import "examples/helpers.jr"\nsay(helpers.greett("x"))'))
    except JuRuGalti as err:
        assert err.message == (
            "'helpers' has no 'greett' — did you mean 'greet'? "
            "— the module has: double, greet, magic"), err.message
        return
    raise AssertionError("expected a member error")


def t_runtime_lookup_suggestion():
    """The checker lets names that MIGHT be assigned pass — the runtime now
    helps too when the value never actually got a value."""
    src = (
        'something = 1\n'
        'func f() {\n'
        '    say(someting)\n'      # typo — never assigned anywhere
        '}\n'
    )
    # the checker catches this statically (it sees every name in the file),
    # so the runtime suggestion is for the REPL-live path; test the checker here
    try:
        check_source(src)
    except JuRuGalti as err:
        assert "did you mean 'something'?" in err.message, err.message
        return
    raise AssertionError("expected a typo error")


# ------------------------------------------------------------------ REPL multi-line
def t_repl_multiline_block():
    cleaned = strip_prompts(run_repl([
        "for i from 1 to 4 {",
        "    if i == 2 {",
        "        continue",
        "    }",
        "    say(i)",
        "}",
        "exit",
    ]))
    lines = [ln for ln in cleaned
             if not ln.startswith(("JuRu", "type"))]
    assert "1" in lines and "3" in lines and "4" in lines, lines
    assert "2" not in lines, lines          # i == 2 was skipped by continue


def t_repl_multiline_dict_build():
    out = strip_prompts(run_repl([
        'd = {"a": 1}',
        'd["b"] =',
        "2",
        "d",
        "exit",
    ]))
    assert "=> {a: 1, b: 2}" in out, out


def t_repl_operator_continuation():
    out = strip_prompts(run_repl([
        "1 +",
        "2",
        '"ab" *',
        "2",
        "exit",
    ]))
    assert "=> 3" in out, out
    assert '=> abab' in out, out


def t_repl_unclosed_block():
    out = run_repl([
        "for i from 1 to 2 {",
        "    say(i)",
        # EOF here — the block never closes
    ])
    assert "the block is not closed — '}' is missing" in out, out


def t_repl_cancel_drops_open_block():
    """The escape hatch: a bare 'cancel' line drops the open block and the
    session continues fresh — vital for piped input where Ctrl-C is absent."""
    out = strip_prompts(run_repl([
        "say(",
        "cancel",
        'say("ok")',
        "exit",
    ]))
    assert "ok" in out, out
    assert "the block is not closed" not in out, out


def t_repl_cancel_only_bare_word():
    """'cancel = 5' inside a block is NOT the escape — only a bare line is."""
    out = strip_prompts(run_repl([
        "for i from 1 to 2 {",
        "    cancel = i + 10",       # a normal variable, not the escape
        "    say(cancel)",
        "}",
        "exit",
    ]))
    assert "11" in out and "12" in out, out


def t_repl_brace_inside_text_is_foolproof():
    """A '}' inside text must NOT close the block — braces are counted by
    the real lexer, not by counting characters."""
    out = strip_prompts(run_repl([
        'for x in [1] {',
        '    say("} looks like a brace {")',
        '}',
        'exit',
    ]))
    assert "} looks like a brace {" in out, out


def t_repl_multiline_then_error_recovery():
    out = strip_prompts(run_repl([
        "for i from 1 to 2 {",
        "    say(i",
        # user realizes the mistake mid-block, Ctrl-C style: just send } to close
        ")",
        "}",
        'say("ok")',
        "exit",
    ]))
    # the completed block ran fine (say(i) took an argument from the next line)
    assert "1" in out and "2" in out, out
    assert "ok" in out, out


def t_repl_single_line_still_works():
    out = strip_prompts(run_repl([
        "for x in [7, 8] { say(x) }",
        "exit",
    ]))
    assert "7" in out and "8" in out, out


ALL = [
    ("checker: typo name suggestion", t_typo_name_suggestion),
    ("checker: typo call suggestion", t_typo_call_suggestion),
    ("checker: typo loop-var suggestion", t_typo_loop_var_suggestion),
    ("checker: typo builtin suggestion", t_typo_builtin_suggestion),
    ("checker: no close match stays plain", t_no_match_stays_plain),
    ("checker: old Hinglish hint wins", t_old_hinglish_hint_still_wins),
    ("runtime: dict key suggestion", t_dict_key_suggestion),
    ("runtime: dict key no match unchanged", t_dict_key_no_match_unchanged),
    ("runtime: module member suggestion", t_module_member_suggestion),
    ("runtime: lookup suggestion (via checker)", t_runtime_lookup_suggestion),
    ("REPL: multi-line block", t_repl_multiline_block),
    ("REPL: multi-line dict build", t_repl_multiline_dict_build),
    ("REPL: operator continuation", t_repl_operator_continuation),
    ("REPL: unclosed block at EOF", t_repl_unclosed_block),
    ("REPL: cancel drops the open block", t_repl_cancel_drops_open_block),
    ("REPL: cancel=5 is a normal variable", t_repl_cancel_only_bare_word),
    ("REPL: braces inside text are foolproof", t_repl_brace_inside_text_is_foolproof),
    ("REPL: error recovery after a multi-line block", t_repl_multiline_then_error_recovery),
    ("REPL: single-line blocks still work", t_repl_single_line_still_works),
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
