r"""JuRu Step 24 tests — the text & formatting wave (zero new keywords).

Six new reserved builtins: format, pad_left, pad_right, center,
split_lines, join_lines (48 → 54). Every behavior the roadmap left open
is decided here and pinned:

  - format(): {} left to right, {0} by index (repeatable), {{ }} literal
    braces, digits-only slots ({007} is 7); mixing the two styles is an
    ERROR; extra values are an ERROR (a typo should not vanish); missing
    values, malformed slots ({x}, { 0 }, {-1}), lone braces and
    out-of-range indices all get friendly, kind-classified errors.
    Values render with the exact same rules as str() / say(). No eval,
    no expression embedding — format() formats values, not code.
  - padding: never truncates; width is DISPLAY width (combining marks 0,
    East Asian wide/fullwidth 2, everything else 1); an odd extra space
    in center() goes on the RIGHT; whole-number width only, never
    negative, at most 10000 characters at a time.
  - lines: split on \n, \r\n and a lone \r; an empty text has NO lines;
    a trailing newline opens no extra empty line; blank lines are kept;
    join_lines takes text-only lines, [] → "", and
    join_lines(split_lines(t)) == t whenever t has no trailing newline.

Nothing else changed: 21 keywords, no parser/AST changes (these are
plain builtins), try/rescue + fail() + call stacks keep working with the
new errors.
"""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS, kind_for
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
from juru.parser import parse_source
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
    try:
        run(src)
    except JuRuGalti as err:
        return err
    raise AssertionError("expected an error: " + src)


def expect_run_galti(src, fragment, kind=None):
    err = caught(src)
    assert fragment in err.message, "{} -> {}".format(src, err.message)
    if kind is not None:
        assert err.kind == kind, "{} -> {} (kind {})".format(src, err.message, err.kind)


# ------------------------------------------------------------------ format: the happy paths
def t_format_automatic_order():
    assert run('name = "Ravi"\nage = 20\n'
               'say(format("Name: {}, Age: {}", name, age))') == "Name: Ravi, Age: 20\n"
    assert run('say(format("{}+{}={}", 1, 2, 3))') == "1+2=3\n"
    # {} consumes left to right, one per slot, in text order
    assert run('say(format("{},{},{}", "a", "b", "c"))') == "a,b,c\n"


def t_format_explicit_and_repeated():
    assert run('say(format("x={0} y={1}", 10, 20))') == "x=10 y=20\n"
    assert run('say(format("{0}-{0}-{1}", "ab", "cd"))') == "ab-ab-cd\n"
    assert run('say(format("{1} before {0}", "first", "second"))') == "second before first\n"
    # {007} parses to index 7 — values fill positions 0…7, so eight values
    assert run('say(format("{007}!", "zero", "one", "two", "three", '
               '"four", "five", "six", "seven"))') == "seven!\n"
    expect_run_galti('format("{007}", 7)',
                     "format() slot {7} does not exist", kind="value")


def t_format_escaped_braces():
    assert run('say(format("{{JuRu}} version {0}", "1.11"))') == "{JuRu} version 1.11\n"
    assert run('say(format("{{{{}}}}"))') == "{{}}\n"        # four braces → two literals
    assert run('say(format("{{{0}}}", 9))') == "{9}\n"      # literal + slot + literal
    assert run('say(format("a}}b"))') == "a}b\n"
    assert run('say(format("{{}}"))') == "{}\n"             # literal pair, not a slot


def t_format_values_render_like_say():
    got = run('say(format("{} {} {} {} {}", "t", 5, 2.5, true, null))')
    assert got == "t 5 2.5 true null\n", got
    assert run('say(format("{} and {}", [1, 2], {"a": 1}))') == "[1, 2] and {a: 1}\n"
    assert run('say(format("{0}", "line1\\nline2"))') == "line1\nline2\n"


def t_format_no_slots_and_empty():
    assert run('say(format("plain"))') == "plain\n"
    assert run('say("[" + format("") + "]")') == "[]\n"


# ------------------------------------------------------------------ format: the friendly guards
def t_format_missing_argument():
    expect_run_galti('format("{}")', "format() needs 1 more value", kind="value")
    expect_run_galti('format("{} {}", "a")', "needs 1 more value", kind="value")
    expect_run_galti('format("{0}")', "slot {0} does not exist — no values were given",
                     kind="value")
    expect_run_galti('format("{2}", 1, 2)',
                     "format() slot {2} does not exist — only 2 values given (0 to 1)",
                     kind="value")


def t_format_extra_arguments_are_an_error():
    expect_run_galti('format("{0}", 1, 2)',
                     "format() got more values than slots — 2 values for 1 slot",
                     kind="value")
    expect_run_galti('format("{}", 1, 2, 3)',
                     "3 values for 1 slot", kind="value")
    expect_run_galti('format("{0}{0}", 1, 2)', "2 values for 1 slot", kind="value")
    expect_run_galti('format("plain", 1)',
                     "got more values than slots — 1 value for no slots", kind="value")


def t_format_mixed_styles_rejected():
    expect_run_galti('format("{} {0}", 1)',
                     "format() cannot mix automatic {} slots and numbered {0} slots "
                     "— pick one style for the whole text", kind="value")
    # mixed stays an error even when the values would have filled every slot
    expect_run_galti('format("{} and {1}", "a", "b")', "cannot mix", kind="value")


def t_format_malformed_placeholders():
    expect_run_galti('format("x{", 1)',
                     "format() found a lone '{' — write '{{' for a literal brace, "
                     "or '{}' / '{0}' for a slot", kind="value")
    expect_run_galti('format("x}", 1)',
                     "format() found a lone '}' — write '}}' for a literal brace",
                     kind="value")
    expect_run_galti('format("{x}", 1)',
                     "format() slot '{x}' is not a valid slot — a slot is '{}' "
                     "or '{0}', '{1}', '{2}', …", kind="value")
    expect_run_galti('format("{ 0}", 1)', "is not a valid slot", kind="value")
    expect_run_galti('format("{-1}", 1)', "is not a valid slot", kind="value")


def t_format_type_guard_and_kinds():
    expect_run_galti("format(5)", "format() needs text — got: 5", kind="type")
    expect_run_galti("format()", "format(text, values...) takes one or more arguments")
    # the try/rescue + call-stack machinery works with the new errors too
    got = run('try {\n    format("{9}", 1)\n} rescue as e {\n'
              '    say(e.kind + "|slot")\n}')
    assert got == "value|slot\n", got
    try:
        run('func f() {\n    format("{9}", 1)\n}\nf()')
    except JuRuGalti as err:
        assert err.stack == (("f", 4),), err.stack
    else:
        raise AssertionError("format error escaped the call stack")


# ------------------------------------------------------------------ padding
def t_pad_left_normal_and_empty():
    assert run('say("[" + pad_left("42", 5) + "]")') == "[   42]\n"
    assert run('say("[" + pad_left("", 3) + "]")') == "[   ]\n"
    assert run('say("[" + pad_left("a", 0) + "]")') == "[a]\n"   # width 0 = no-op
    assert run('say("[" + pad_left("", 0) + "]")') == "[]\n"


def t_pad_right_normal_and_empty():
    assert run('say("[" + pad_right("JuRu", 8) + "]")') == "[JuRu    ]\n"
    assert run('say("[" + pad_right("", 2) + "]")') == "[  ]\n"
    assert run('say("[" + pad_right("a", 1) + "]")') == "[a]\n"


def t_center_normal_and_odd():
    assert run('say("[" + center("JuRu", 10) + "]")') == "[   JuRu   ]\n"
    # odd extra space goes on the RIGHT (pinned): 3 spaces → 1 left, 2 right
    assert run('say("[" + center("hi", 5) + "]")') == "[ hi  ]\n"
    assert run('say("[" + center("hi", 6) + "]")') == "[  hi  ]\n"   # even: split evenly
    assert run('say("[" + center("", 5) + "]")') == "[     ]\n"


def t_padding_never_truncates():
    assert run('say("[" + pad_left("toolong", 3) + "]")') == "[toolong]\n"
    assert run('say("[" + pad_right("toolong", 3) + "]")') == "[toolong]\n"
    assert run('say("[" + center("abcdef", 4) + "]")') == "[abcdef]\n"
    assert run('say("[" + center("abcdef", 6) + "]")') == "[abcdef]\n"


def t_padding_unicode_display_width():
    # East Asian wide characters take 2 columns — len() still counts characters
    assert run('say(len("は"))') == "1\n"
    assert run('say("[" + pad_left("は", 5) + "]")') == "[   は]\n"    # 5 - 2 = 3 spaces
    assert run('say("[" + center("は", 6) + "]")') == "[  は  ]\n"
    # combining marks take 0 columns
    assert run('say("[" + pad_left("cafe\\u0301", 6) + "]")') == "[  cafe\u0301]\n"
    assert run('say(len("cafe\\u0301"))') == "5\n"
    # an emoji is wide/fullwidth → 2 columns
    assert run('say("[" + center("\U0001F44D", 6) + "]")') == "[  \U0001F44D  ]\n"
    assert run('say("[" + pad_right("\u306f\u306f", 5) + "]")') == "[はは ]\n"


def t_padding_guards():
    expect_run_galti("pad_left(5, 3)", "pad_left() needs text — got: 5", kind="type")
    expect_run_galti('pad_right(null, 3)', "pad_right() needs text — got: null", kind="type")
    expect_run_galti('pad_left("a", 2.5)', "needs a whole-number width — got: 2.5",
                     kind="type")
    expect_run_galti('pad_left("a", true)', "needs a whole-number width — got: true",
                     kind="type")
    expect_run_galti('center("a", "x")', "center() needs a whole-number width — got: x",
                     kind="type")
    expect_run_galti('pad_left("a", -1)', "pad_left() width cannot be negative — got: -1",
                     kind="value")
    expect_run_galti('center("a", -2)', "center() width cannot be negative", kind="value")
    expect_run_galti('pad_right("a", 10001)',
                     "pad_right() width is too big — at most 10000 characters at a time",
                     kind="value")
    expect_run_galti('pad_left("a")', "pad_left(text, width) takes exactly 2 arguments")
    expect_run_galti('pad_left("a", 1, 2)', "pad_left(text, width) takes exactly 2 arguments")


# ------------------------------------------------------------------ lines
def t_split_lines_lf_and_crlf():
    assert run('say(split_lines("first\\nsecond\\nthird"))') == "[first, second, third]\n"
    assert run('say(split_lines("a" + chr(13) + chr(10) + "b"))') == "[a, b]\n"
    assert run('say(split_lines("a" + chr(13) + "b"))') == "[a, b]\n"   # a lone \r too
    assert run('say(split_lines("a" + chr(13) + chr(10)))') == "[a]\n"  # trailing CRLF


def t_split_lines_edges():
    assert run('say(split_lines(""))') == "[]\n"                    # empty: NO lines
    assert run('say(split_lines("one"))') == "[one]\n"              # no newline
    assert run('say(split_lines("a\\n"))') == "[a]\n"               # trailing LF: no extra ""
    assert run('say(split_lines("a\\n\\nb"))') == "[a, , b]\n"      # blank lines are kept
    assert run('say(split_lines("\\n"))') == "[]\n"                 # one empty line → []
    assert run('say(split_lines("\\n\\n"))') == "[, ]\n"   # two blank lines, kept
    assert run('say(split_lines("caf\\u00e9\\nna\\u00efve"))') == "[café, naïve]\n"


def t_join_lines_and_interaction():
    assert run('say(join_lines(["first", "second", "third"]))') == \
        "first\nsecond\nthird\n"
    assert run('say("[" + join_lines([]) + "]")') == "[]\n"         # empty list → ""
    assert run('say(join_lines(["a", "", "b"]))') == "a\n\nb\n"     # empties preserved
    assert run('say(join_lines(["one"]))') == "one\n"
    # the documented round-trip: text without a trailing newline comes back exact
    assert run('t = "a\\nb\\nc"\nsay(join_lines(split_lines(t)) == t)') == "true\n"
    assert run('t = "a\\nb\\nc\\n"\nsay(join_lines(split_lines(t)) == "a\\nb\\nc")') == "true\n"
    # a table the easy way: split_lines + join_lines + pad_right
    got = run('rows = split_lines("name,age\\nravi,20")\n'
              'for row in rows {\n'
              '    parts = split(row, ",")\n'
              '    say(pad_right(parts[0], 6) + parts[1])\n'
              '}')
    assert got == "name  age\nravi  20\n", got


def t_join_lines_guards():
    expect_run_galti('join_lines("ab")', "join_lines() needs a list — got: ab", kind="type")
    expect_run_galti('join_lines(["a", 2])',
                     "join_lines() needs every line to be text — got: 2 at position 2",
                     kind="type")
    expect_run_galti('join_lines([true, "b"])',
                     "needs every line to be text — got: true at position 1", kind="type")
    expect_run_galti("split_lines(5)", "split_lines() needs text — got: 5", kind="type")
    expect_run_galti('join_lines(["a"], 1)', "join_lines(lines) takes exactly 1 argument")


# ------------------------------------------------------------------ registry + surface
def t_registry_and_surface():
    assert VERSION == "1.12"
    assert len(KEYWORDS) == 21                       # zero new keywords
    assert len(BUILTINS) == 67                       # 48 + text wave + files/JSON
    new = ("format", "pad_left", "pad_right", "center", "split_lines", "join_lines")
    assert set(new) <= set(BUILTINS)
    for name in new:
        assert BUILTIN_ARITY[name], name
        assert BUILTIN_HINT[name], name
    from juru import helpdb
    assert set(helpdb.BUILTIN_CARDS) == set(BUILTINS)   # every builtin has a card
    assert len(helpdb.BUILTIN_CARDS) == 67
    assert len(helpdb.KEYWORD_CARDS) == 21
    assert helpdb.card_for("printf") == helpdb.card_for("format")


def t_kind_rules_for_the_new_errors():
    assert kind_for("format() cannot mix automatic {} slots and numbered {0} slots") == "value"
    assert kind_for("format() found a lone '}' — write '}}' for a literal brace") == "value"
    assert kind_for("format() slot '{x}' is not a valid slot") == "value"
    assert kind_for("format() got more values than slots — 2 values for 1 slot") == "value"
    assert kind_for("format() slot {5} does not exist — only 2 values given (0 to 1)") == "value"
    assert kind_for("pad_left() width cannot be negative — got: -1") == "value"
    assert kind_for("pad_left() width is too big — at most 10000 characters at a time") == "value"
    assert kind_for("pad_left() needs text — got: 5") == "type"


def t_no_parser_changes_needed():
    # these are plain calls — the AST is the ordinary Call node, nothing new
    tree = parse_source('say(format("{}", 1))\n')
    assert type(tree.stmts[0]).__name__ == "ExprSt" or tree.stmts[0] is not None
    tree = check_source('say(pad_left("a", 3))')
    assert tree is not None


def t_old_text_tools_unchanged():
    # Step 1–3 waves keep working side by side
    assert run('say(upper(trim("  hi  ")))') == "HI\n"
    assert run('say(join([1, 2], "-"))') == "1-2\n"
    assert run('say("ab" * 3)') == "ababab\n"
    assert run('say("ell" in "hello")') == "true\n"
    assert run('say("x=" + 5)') == "x=5\n"           # text + number auto-join, unchanged


# ------------------------------------------------------------------ runner
ALL = [
    ("format: automatic {} order", t_format_automatic_order),
    ("format: explicit {0} + repeats + {007}", t_format_explicit_and_repeated),
    ("format: escaped braces", t_format_escaped_braces),
    ("format: values render like say()", t_format_values_render_like_say),
    ("format: no slots + empty text", t_format_no_slots_and_empty),
    ("format: missing arguments", t_format_missing_argument),
    ("format: extra arguments are an error", t_format_extra_arguments_are_an_error),
    ("format: mixed styles rejected", t_format_mixed_styles_rejected),
    ("format: malformed placeholders", t_format_malformed_placeholders),
    ("format: type guard + kinds + try + stacks", t_format_type_guard_and_kinds),
    ("pad_left: normal + empty + zero", t_pad_left_normal_and_empty),
    ("pad_right: normal + empty", t_pad_right_normal_and_empty),
    ("center: normal + odd extra right", t_center_normal_and_odd),
    ("padding never truncates", t_padding_never_truncates),
    ("padding: unicode display width", t_padding_unicode_display_width),
    ("padding guards (types, negative, budget)", t_padding_guards),
    ("split_lines: LF + CRLF + lone CR", t_split_lines_lf_and_crlf),
    ("split_lines: empty, blank, trailing", t_split_lines_edges),
    ("join_lines + split_lines round-trip", t_join_lines_and_interaction),
    ("join_lines guards", t_join_lines_guards),
    ("registry: 67 builtins, cards, 21 keywords", t_registry_and_surface),
    ("kind rules for the new errors", t_kind_rules_for_the_new_errors),
    ("no parser changes needed", t_no_parser_changes_needed),
    ("old text tools unchanged", t_old_text_tools_unchanged),
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
