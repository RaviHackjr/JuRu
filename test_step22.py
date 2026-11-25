r"""JuRu Step 22 tests — collections & ergonomics wave 1.

Every feature of the wave is guarded twice (checker + runtime), with the
friendly error messages pinned byte-for-byte:
  - augmented assignment: x += e, xs[i] -= e, d["k"] *= e (RHS read after
    the old value, exactly once)
  - negative indexing: -1 is the last item, only past the start is out of range
  - slice steps: [::-1], [::2], [1:7:2] — Python semantics, zero step refused
  - 17 new builtins: insert, remove_at, clear, extend, unique, delete,
    items, merge, index_of, starts_with, ends_with, ord, chr, set_of,
    union, intersect, difference
  - sets: no duplicates, order kept, one equality for the whole language
  - \uXXXX escapes (exactly 4 hex digits, surrogates refused)
  - backward compatibility: the old plain forms are byte-identical
"""
import contextlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
from juru.parser import parse_source, dump
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


def run(src):
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=HERE)
    return buf.getvalue()


def expect_run_galti(src, fragment):
    try:
        run(src)
    except JuRuGalti as err:
        assert fragment in err.message, "{} -> {}".format(src, err.message)
        return
    raise AssertionError("expected a runtime error: " + src)


def expect_check_galti(src, fragment):
    try:
        check_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "{} -> {}".format(src, err.message)
        return
    raise AssertionError("expected a semantic error: " + src)


def expect_galti(src, fragment):
    expect_check_galti(src, fragment)
    expect_run_galti(src, fragment)


# ------------------------------------------------------------------ augmented assignment
def t_aug_all_five_ops():
    assert run("x = 5\nx += 2\nsay(x)") == "7\n"
    assert run("x = 5\nx -= 3\nsay(x)") == "2\n"
    assert run("x = 5\nx *= 2\nsay(x)") == "10\n"
    assert run("x = 5\nx /= 4\nsay(x)") == "1.25\n"
    assert run("x = 7\nx %= 4\nsay(x)") == "3\n"


def t_aug_text_join():
    assert run('x = "ab"\nx += "cd"\nsay(x)') == "abcd\n"
    assert run('x = "n"\nx += 5\nsay(x)') == "n5\n"


def t_aug_in_a_loop():
    assert run("i = 0\nwhile i < 3 {\n    i += 1\n}\nsay(i)") == "3\n"
    assert run("total = 0\nfor i from 1 to 4 {\n    total += i\n}\nsay(total)") == "10\n"


def t_aug_list_index():
    assert run("xs = [1, 2, 3]\nxs[0] += 10\nsay(xs)") == "[11, 2, 3]\n"
    assert run("xs = [1, 2, 3]\nxs[-1] += 5\nsay(xs)") == "[1, 2, 8]\n"
    assert run("xs = [1, 2]\nxs[1] *= 3\nsay(xs)") == "[1, 6]\n"


def t_aug_dict_key():
    assert run('d = {"n": 1}\nd["n"] += 4\nsay(d)') == "{n: 5}\n"
    assert run('d = {"n": 6}\nd["n"] /= 2\nsay(d)') == "{n: 3.0}\n"


def t_aug_read_old_value_first():
    """The old value is read BEFORE the right side — and the right side is
    evaluated exactly once (x += 2 must be 7, never 12)."""
    assert run("x = 5\nx += 2\nx += 3\nsay(x)") == "10\n"
    assert run("x = 2\ny = 3\nx += y\nsay(x)") == "5\n"


def t_aug_missing_dict_key():
    expect_run_galti('d = {"n": 1}\nd["z"] += 1',
                     "key 'z' was not found — this dict has: n")


def t_aug_out_of_range_index():
    expect_run_galti("xs = [1, 2, 3]\nxs[7] += 1", "out of range")
    expect_run_galti("xs = [1, 2, 3]\nxs[-4] += 1", "out of range")


def t_aug_undefined_name():
    expect_run_galti("x += 2", "'x' was not found")


def t_aug_reserved_names():
    expect_check_galti("min += 1", "'min' is reserved (builtin) — pick another name")
    expect_check_galti("insert += 1", "'insert' is reserved (builtin) — pick another name")
    expect_check_galti("set_of = 5", "'set_of' is reserved (builtin) — pick another name")


def t_aug_member_write_still_refused():
    expect_check_galti('d = {}\nd.name += 1', "'data.key = value' does not work")


# ------------------------------------------------------------------ negative indexing
def t_negative_index_list():
    assert run("xs = [1, 2, 3]\nsay(xs[-1])") == "3\n"
    assert run("xs = [1, 2, 3]\nsay(xs[-3])") == "1\n"
    assert run("xs = [1, 2, 3]\nsay(xs[-2])") == "2\n"


def t_negative_index_text():
    assert run('say("hello"[-1])') == "o\n"
    assert run('say("hello"[-5])') == "h\n"


def t_negative_out_of_range_message():
    expect_run_galti("say([1, 2, 3][-4])",
                 "index -4 is out of range — this list has 3 items (-3 to 2)")
    expect_run_galti('say("hi"[-3])',
                 "index -3 is out of range — this text has 2 items (-2 to 1)")


def t_negative_index_write():
    assert run("xs = [1, 2, 3]\nxs[-1] = 9\nsay(xs)") == "[1, 2, 9]\n"
    assert run("xs = [1, 2, 3]\nxs[-3] = 0\nsay(xs)") == "[0, 2, 3]\n"


# ------------------------------------------------------------------ slice steps
def t_slice_reverse():
    assert run("say([1, 2, 3, 4, 5][::-1])") == "[5, 4, 3, 2, 1]\n"
    assert run('say("abcdef"[::-1])') == "fedcba\n"


def t_slice_step_positive():
    assert run("say([1, 2, 3, 4, 5][::2])") == "[1, 3, 5]\n"
    assert run("say([1, 2, 3, 4, 5][1:4:2])") == "[2, 4]\n"
    assert run('say("abcdef"[1:5:2])') == "bd\n"


def t_slice_negative_bounds():
    assert run("say([1, 2, 3, 4, 5][-3:])") == "[3, 4, 5]\n"
    assert run("say([1, 2, 3, 4, 5][:-2])") == "[1, 2, 3]\n"
    assert run("say([1, 2, 3, 4, 5][-3:-1])") == "[3, 4]\n"
    assert run('say("abcdef"[-3:])') == "def\n"


def t_slice_step_negative_start():
    assert run("say([1, 2, 3, 4, 5][-2::-2])") == "[4, 2]\n"
    assert run("say([1, 2, 3, 4, 5][4::-1])") == "[5, 4, 3, 2, 1]\n"
    assert run("say([1, 2, 3, 4, 5][:2:-1])") == "[5, 4]\n"


def t_slice_step_zero():
    expect_run_galti("say([1, 2, 3][0:2:0])", "the slice step cannot be zero")
    expect_run_galti('say("ab"[::0])', "the slice step cannot be zero")


def t_slice_non_int_parts():
    expect_run_galti("say([1, 2, 3][::1.5])",
                 "the slice step must be a whole number (int) — got: 1.5")
    expect_run_galti('say([1, 2, 3]["x":2])',
                 "the slice start must be a whole number (int) — got: x")
    expect_run_galti('say([1, 2, 3][0:"x"])',
                 "the slice end must be a whole number (int) — got: x")
    expect_run_galti("say([1, 2, 3][::true])",
                 "the slice step must be a whole number (int) — got: true")


def t_slice_clamps_still_hold():
    """The old promise: out-of-range slices never crash, they give what exists."""
    assert run("say([1, 2, 3][1:99])") == "[2, 3]\n"
    assert run('say("hi"[:99])') == "hi\n"
    assert run("say([1, 2, 3][9:99])") == "[]\n"
    assert run("say([1, 2, 3][-99:])") == "[1, 2, 3]\n"
    assert run("say([1, 2, 3][:-99])") == "[]\n"


def t_slice_full_and_plain():
    assert run("say([1, 2, 3][:])") == "[1, 2, 3]\n"
    assert run('say("abc"[:])') == "abc\n"
    assert run("say([10, 20, 30, 40][1:3])") == "[20, 30]\n"     # old plain form
    assert run("say([1, 2, 3][1])") == "2\n"                     # old plain index
    assert run('say("hello"[1:4])') == "ell\n"


def t_slice_assignment_quirk():
    """`xs[0:1] = [9]` has always meant `xs[0] = [9]` — only the start
    bound is used, exactly as in v1.8. A slice never assigns a range."""
    assert run("xs = [1, 2]\nxs[0:1] = [9]\nsay(xs)") == "[[9], 2]\n"


# ------------------------------------------------------------------ list tools
def t_insert_basic():
    assert run("xs = [1, 2, 3]\ninsert(xs, 0, 9)\nsay(xs)") == "[9, 1, 2, 3]\n"
    assert run("xs = [1, 2, 3]\nsay(insert(xs, 1, 9))") == "[1, 9, 2, 3]\n"
    assert run("xs = [1, 2, 3]\ninsert(xs, -1, 7)\nsay(xs)") == "[1, 2, 7, 3]\n"
    assert run("xs = [1, 2]\nsay(insert(xs, 99, 0))") == "[1, 2, 0]\n"
    assert run("xs = [1, 2]\nsay(insert(xs, -99, 0))") == "[0, 1, 2]\n"


def t_insert_guards():
    expect_run_galti("insert(5, 0, 1)", "insert() needs a list — got: 5")
    expect_run_galti("insert([1], 1.5, 0)",
                 "insert() needs a whole number (int) — got: 1.5")
    expect_run_galti("insert([1], true, 0)",
                 "insert() needs a whole number (int) — got: true")


def t_remove_at_basic():
    assert run("xs = [10, 20, 30]\nsay(remove_at(xs, 1))\nsay(xs)") == "20\n[10, 30]\n"
    assert run("xs = [10, 20, 30]\nsay(remove_at(xs, -1))\nsay(xs)") == "30\n[10, 20]\n"
    assert run("say(remove_at([\"a\", \"b\"], 0))") == "a\n"


def t_remove_at_guards():
    expect_run_galti("remove_at(5, 0)", "remove_at() needs a list — got: 5")
    expect_run_galti("remove_at([1, 2, 3], 5)",
                 "index 5 is out of range — this list has 3 items (0 to 2)")
    expect_run_galti("remove_at([1, 2, 3], -4)",
                 "index -4 is out of range — this list has 3 items (-3 to 2)")


def t_clear_basic():
    assert run("xs = [1, 2, 3]\nclear(xs)\nsay(xs)") == "[]\n"
    assert run("xs = []\nclear(xs)\nsay(xs)") == "[]\n"


def t_clear_guards():
    expect_run_galti("clear(5)", "clear() needs a list — got: 5")


def t_extend_basic():
    assert run("xs = [1, 2]\nextend(xs, [3, 4])\nsay(xs)") == "[1, 2, 3, 4]\n"
    assert run("xs = []\nextend(xs, [])\nsay(xs)") == "[]\n"


def t_extend_guards():
    expect_run_galti("extend(5, [1])", "extend() needs a list — got: 5")
    expect_run_galti("extend([1], 2)", "the extend items must be a list — got: 2")


def t_unique_basic():
    assert run("say(unique([1, 2, 1, 3, 2]))") == "[1, 2, 3]\n"
    assert run('say(unique(["a", "a", "b"]))') == "[a, b]\n"
    assert run("xs = [1, 1]\nsay(unique(xs))\nsay(xs)") == "[1]\n[1, 1]\n"  # NEW list


def t_unique_uses_the_one_equality():
    assert run("say(unique([1, 1.0, 2]))") == "[1, 2]\n"      # 1 == 1.0
    assert run("say(unique([true, 1, 2]))") == "[true, 1, 2]\n"  # true != 1
    assert run("say(unique([[1], [1], [2]]))") == "[[1], [2]]\n"


def t_unique_guards():
    expect_run_galti("unique(5)", "unique() needs a list — got: 5")


# ------------------------------------------------------------------ dict tools
def t_delete_basic():
    assert run('d = {"a": 1, "b": 2}\ndelete(d, "a")\nsay(d)') == "{b: 2}\n"
    assert run('d = {"a": 1}\nsay(delete(d, "a"))') == "{}\n"


def t_delete_guards():
    expect_run_galti("delete([1], 0)", "delete() needs a dict — got: [1]")
    expect_run_galti('d = {"a": 1}\ndelete(d, "z")',
                 "key 'z' was not found — this dict has: a")
    expect_run_galti('delete({}, "a")', "key 'a' was not found — this dict is empty")
    expect_run_galti("d = {}\ndelete(d, 1.5)",
                 "a dict key must be text or a whole number — got: 1.5")


def t_items_basic():
    assert run('say(items({"a": 1, "b": 2}))') == "[[a, 1], [b, 2]]\n"
    assert run("say(items({}))") == "[]\n"
    assert run('for pair in items({"x": 9}) {\n    say(pair[0])\n}') == "x\n"


def t_items_guards():
    expect_run_galti("items([1])", "items() needs a dict — got: [1]")


def t_merge_basic():
    assert run('say(merge({"a": 1}, {"b": 2}))') == "{a: 1, b: 2}\n"
    assert run('say(merge({"a": 1}, {"a": 9, "b": 2}))') == "{a: 9, b: 2}\n"
    assert run('a = {"a": 1}\nb = {"b": 2}\nmerge(a, b)\nsay(a)\nsay(b)') \
        == "{a: 1}\n{b: 2}\n"                                # a NEW dict


def t_merge_guards():
    expect_run_galti("merge({}, 5)", "merge() needs dicts — got: dict and int")
    expect_run_galti("merge([1], {})", "merge() needs dicts — got: list and dict")


# ------------------------------------------------------------------ text tools
def t_index_of_basic():
    assert run('say(index_of("hello", "ll"))') == "2\n"
    assert run('say(index_of("hello", "h"))') == "0\n"
    assert run('say(index_of("hello", "z"))') == "-1\n"


def t_index_of_guards():
    expect_run_galti('index_of(5, "x")', "index_of() needs text — got: 5")
    expect_run_galti('index_of("hi", 5)', "the index_of piece must be text — got: 5")
    expect_run_galti('index_of("hi", "")', "the index_of piece cannot be empty")


def t_starts_ends_basic():
    assert run('say(starts_with("hello", "he"))') == "true\n"
    assert run('say(starts_with("hello", "lo"))') == "false\n"
    assert run('say(ends_with("photo.png", ".png"))') == "true\n"
    assert run('say(ends_with("photo.png", ".jpg"))') == "false\n"


def t_starts_ends_guards():
    expect_run_galti('starts_with(5, "a")', "starts_with() needs text — got: 5")
    expect_run_galti('starts_with("hi", 5)',
                 "the starts_with prefix must be text — got: 5")
    expect_run_galti('starts_with("hi", "")', "the starts_with prefix cannot be empty")
    expect_run_galti('ends_with(5, "a")', "ends_with() needs text — got: 5")
    expect_run_galti('ends_with("hi", 5)',
                 "the ends_with suffix must be text — got: 5")
    expect_run_galti('ends_with("hi", "")', "the ends_with suffix cannot be empty")


def t_ord_chr_pair():
    assert run('say(ord("A"))') == "65\n"
    assert run('say(ord("a"))') == "97\n"
    assert run("say(chr(65))") == "A\n"
    assert run("say(chr(97))") == "a\n"
    assert run("say(chr(128512))") == "\U0001F600\n"    # an emoji — codes go far
    assert run("say(chr(0))") == "\x00\n"
    assert run('say(chr(ord("Q")))') == "Q\n"


def t_ord_chr_guards():
    expect_run_galti('ord("ab")', "ord() needs exactly one character — got 2")
    expect_run_galti('ord("")', "ord() needs exactly one character — got 0")
    expect_run_galti("ord(5)", "ord() needs text — got: 5")
    expect_run_galti("say(chr(1114112))",
                 "chr(1114112) — the code must be between 0 and 1114111")
    expect_run_galti("say(chr(-1))",
                 "chr(-1) — the code must be between 0 and 1114111")
    expect_run_galti("say(chr(55296))",
                 "chr(55296) — codes 55296 to 57343 are reserved; "
                 "this character cannot be shown")
    expect_run_galti("say(chr(1.5))", "chr() needs a whole number (int) — got: 1.5")
    expect_run_galti("say(chr(true))", "chr() needs a whole number (int) — got: true")


# ------------------------------------------------------------------ sets
def t_set_display_and_dedupe():
    assert run("say(set_of([3, 1, 3, 2]))") == "{3, 1, 2}\n"
    assert run("say(set_of([]))") == "set()\n"
    assert run("say(set_of([1, 1, 1]))") == "{1}\n"


def t_set_order_is_first_seen():
    assert run("say(set_of([2, 2, 1, 3, 1]))") == "{2, 1, 3}\n"


def t_set_equality_rules():
    assert run("say(set_of([1, 2]) == set_of([2, 1]))") == "true\n"
    assert run("say(set_of([1]) == set_of([1, 2]))") == "false\n"
    assert run("say(set_of([]) == set_of([]))") == "true\n"
    assert run("say(set_of([true]) == set_of([1]))") == "false\n"   # true != 1
    assert run("say(set_of([1]) == set_of([1.0]))") == "true\n"     # 1 == 1.0
    assert run("say(set_of([1]) == [1])") == "false\n"              # set != list


def t_set_len_membership_truthy():
    assert run("s = set_of([1, 2])\nsay(len(s))") == "2\n"
    assert run("say(len(set_of([1, 2, 2])))") == "2\n"
    assert run("s = set_of([1])\nsay(1 in s)\nsay(9 in s)") == "true\nfalse\n"
    assert run('s = set_of(["a"])\nsay("a" in s)') == "true\n"
    assert run('if set_of([]) { say("t") } else { say("empty set is false") }') \
        == "empty set is false\n"
    assert run('if set_of([1]) { say("non-empty is true") }') == "non-empty is true\n"


def t_set_for_in():
    assert run("for x in set_of([3, 1, 2]) {\n    say(x)\n}") == "3\n1\n2\n"
    assert run("total = 0\nfor x in set_of([1, 2, 3]) {\n    total += x\n}\nsay(total)") \
        == "6\n"


def t_set_sorted_is_a_new_list():
    assert run("say(sorted(set_of([3, 1, 2])))") == "[1, 2, 3]\n"
    assert run("s = set_of([3, 1])\nsay(sorted(s))\nsay(s)") == "[1, 3]\n{3, 1}\n"
    assert run('say(sorted(set_of(["b", "a"])))') == "[a, b]\n"


def t_set_type():
    assert run("say(type(set_of([1])))") == "set\n"
    assert run("say(type(set_of([])))") == "set\n"


def t_set_ops():
    assert run("a = set_of([1, 2, 3])\nb = set_of([3, 4])\nsay(union(a, b))") \
        == "{1, 2, 3, 4}\n"
    assert run("a = set_of([1, 2, 3])\nb = set_of([3, 4])\nsay(intersect(a, b))") \
        == "{3}\n"
    assert run("a = set_of([1, 2, 3])\nb = set_of([3, 4])\nsay(difference(a, b))") \
        == "{1, 2}\n"
    assert run("say(union(set_of([]), set_of([])))") == "set()\n"
    # originals are never touched
    assert run("a = set_of([1])\nb = set_of([2])\nunion(a, b)\nsay(a)\nsay(b)") \
        == "{1}\n{2}\n"


def t_set_ops_guards():
    expect_run_galti("union([1], [2])",
                 "union() needs two sets — got: list and list "
                 "(build one with set_of([...]))")
    expect_run_galti("intersect(5, set_of([1]))",
                 "intersect() needs two sets — got: int and set "
                 "(build one with set_of([...]))")
    expect_run_galti("difference(set_of([1]), [1])",
                 "difference() needs two sets — got: set and list "
                 "(build one with set_of([...]))")


def t_set_plus_refused():
    expect_run_galti("a = set_of([1])\nb = set_of([2])\nsay(a + b)",
                 "cannot use '+' on set and set")


def t_set_index_refused():
    expect_run_galti("s = set_of([1])\nsay(s[0])",
                 "only lists and text support indexing — got set")


def t_no_set_literal():
    """{} is a dict, forever — sets are born from set_of([...])."""
    assert run("say(type({}))") == "dict\n"
    assert run('say(type({"a": 1}))') == "dict\n"


# ------------------------------------------------------------------ \uXXXX escapes
def t_unicode_escape_works():
    assert run('say("\\u0041")') == "A\n"
    assert run('say("\\u00e9")') == "é\n"
    assert run('say("\\u4e2d")') == "中\n"
    assert run('say("a\\u0041b")') == "aAb\n"


def t_unicode_escape_needs_four_hex_digits():
    expect_galti('say("\\uzzzz")',
                 "the \\u escape needs 4 hex digits — like \\u0041")
    expect_galti('say("\\u00")',
                 "the \\u escape needs 4 hex digits — like \\u0041")
    expect_galti('say("\\u00g1")',
                 "the \\u escape needs 4 hex digits — like \\u0041")


def t_unicode_escape_surrogates_refused():
    expect_galti('say("\\ud800")',
                 "\\ud800 is a reserved code (55296 to 57343) — "
                 "pick another character")
    expect_galti('say("\\udfff")',
                 "\\udfff is a reserved code (55296 to 57343) — "
                 "pick another character")


def t_escape_hint_lists_u():
    expect_galti('say("\\q")',
                 "I do not know the escape '\\q' — only \\n, \\t, \\\", \\\\ and \\u work")


# ------------------------------------------------------------------ registry / grammar / dump
def t_registry_tables_agree():
    assert len(BUILTINS) == 54     # 47 + fail (Step 23) + the text wave (Step 24)
    assert set(BUILTIN_ARITY) == set(BUILTINS)
    assert set(BUILTIN_HINT) == set(BUILTINS)
    for name, (lo, hi) in BUILTIN_ARITY.items():
        assert isinstance(lo, int) and lo >= 0
        assert hi is None or (isinstance(hi, int) and hi >= lo)
    for name in ("insert", "remove_at", "clear", "extend", "unique", "delete",
                 "items", "merge", "index_of", "starts_with", "ends_with",
                 "ord", "chr", "set_of", "union", "intersect", "difference"):
        assert name in BUILTINS, name
    assert BUILTIN_ARITY["min"] == (1, None) and BUILTIN_ARITY["max"] == (1, None)


def t_min_max_variadic():
    assert run("say(min(3))") == "3\n"
    assert run("say(max(4, 2, 9, 1))") == "9\n"
    assert run("say(min([7, 2, 4]))") == "2\n"
    assert run("say(max([7, 2, 4]))") == "7\n"
    assert run("say(min(3, 9))") == "3\n"                 # the old way, unchanged
    assert run("say(max(3, 9))") == "9\n"
    expect_run_galti("say(min([]))",
                 "min() — this list is empty, there is nothing to compare")
    expect_run_galti("say(max([]))",
                 "max() — this list is empty, there is nothing to compare")
    expect_run_galti('say(min("a", 1))', "min() needs numbers — got text and int")
    expect_run_galti('say(max(1, "b"))', "max() needs numbers — got int and text")
    expect_run_galti("say(max([1], 2))", "max() needs numbers — got list and int")
    expect_run_galti('say(min(1, "a", 2))', "min() needs numbers — got: text")
    expect_galti("say(min())",
                 "min() takes one or more arguments — like min(a, b) or min(list)")
    expect_galti("say(max())",
                 "max() takes one or more arguments — like max(a, b) or max(list)")
    expect_run_galti("say(min([1, true]))",
                 "min() needs only numbers — found: true")


def t_mirror_rule_for_the_new_builtins():
    """Wrong arity: checker message == runtime message == hint."""
    new_tools = ("insert", "remove_at", "clear", "extend", "unique", "delete",
                 "items", "merge", "index_of", "starts_with", "ends_with",
                 "ord", "chr", "set_of", "union", "intersect", "difference")
    for name in new_tools:
        lo, hi = BUILTIN_ARITY[name]
        hint = BUILTIN_HINT[name]
        too_few = "{}({})".format(name, ", ".join(["1"] * (lo - 1)))
        too_many = "{}({})".format(name, ", ".join(["1"] * (hi + 1)))
        for call in (too_few, too_many):
            expect_check_galti(call, hint)
            expect_run_galti(call, hint)


def t_grammar_colors_the_language():
    with open(os.path.join(HERE, "vscode", "juru-vscode", "syntaxes",
                           "juru.tmLanguage.json"), encoding="utf-8") as f:
        grammar = json.load(f)
    kw = grammar["repository"]["keywords"]["match"]
    head, tail = "\\b(", ")\\b"
    colored = set(kw[len(head):-len(tail)].split("|"))
    assert colored == set(KEYWORDS), "grammar keywords drifted"
    builtin = grammar["repository"]["builtin"]["match"]
    for name in BUILTINS:
        assert name in builtin.split("(")[1], "grammar misses builtin: " + name
    op = grammar["repository"]["operator"]["match"]
    for aug in ("\\+=", "\\-=", "\\*=", "/=", "%="):
        assert aug in op, "grammar operator misses " + aug


def t_dump_forms():
    tree = parse_source("x += 2\n")
    assert dump(tree.stmts[0]) == "(augassign + x (num 2))", dump(tree.stmts[0])
    tree = parse_source("xs[0] += 10\n")
    assert dump(tree.stmts[0]) == "(augsetindex + (name xs) (num 0) (num 10))"
    tree = parse_source("xs[1:7:2]\n")
    assert dump(tree.stmts[0].expr) == "(slice-step (name xs) (num 1) (num 7) (num 2))"
    # the plain forms are byte-identical to the old ones
    tree = parse_source("x = 2\n")
    assert dump(tree.stmts[0]) == "(assign x (num 2))"
    tree = parse_source("xs[0] = 10\n")
    assert dump(tree.stmts[0]) == "(setindex (name xs) (num 0) (num 10))"
    tree = parse_source("xs[1:7]\n")
    assert dump(tree.stmts[0].expr) == "(slice (name xs) (num 1) (num 7))"
    tree = parse_source("xs[1]\n")
    assert dump(tree.stmts[0].expr) == "(index (name xs) (num 1))"


def t_dump_forms_all_five_ops():
    for op in ("+", "-", "*", "/", "%"):
        tree = parse_source("x {}= 2\n".format(op))
        assert dump(tree.stmts[0]) == "(augassign {} x (num 2))".format(op), op
        tree = parse_source("xs[0] {}= 2\n".format(op))
        assert dump(tree.stmts[0]) == \
            "(augsetindex {} (name xs) (num 0) (num 2))".format(op), op


def t_backward_compat_plain_programs():
    """A program with none of the new syntax behaves exactly as before."""
    assert run("x = 5\nsay(x)") == "5\n"
    assert run("xs = [1, 2]\nxs[0] = 9\nsay(xs)") == "[9, 2]\n"
    assert run("xs = [1, 2, 3]\nsay(xs[1:])\nsay(xs[0:2])") == "[2, 3]\n[1, 2]\n"
    assert run('s = "hello"\nsay(s[0])\nsay(s[1:3])') == "h\nel\n"
    assert run("d = {}\nd[\"k\"] = 1\nsay(d)") == "{k: 1}\n"
    assert run("say(1 + 2 * 3 - 4 / 2)") == "5.0\n"
    assert run("for i from 1 to 3 {\n    say(i)\n}") == "1\n2\n3\n"


def t_version_and_surface():
    assert VERSION == "1.11"
    assert len(KEYWORDS) == 21          # Step 23 (v1.10) added try + rescue
    assert len(BUILTINS) == 54          # Step 24 (v1.11) added the text wave


# ------------------------------------------------------------------ runner
ALL = [
    ("augmented assign: all five ops", t_aug_all_five_ops),
    ("augmented assign: text join", t_aug_text_join),
    ("augmented assign: loop counters", t_aug_in_a_loop),
    ("augmented assign: list index", t_aug_list_index),
    ("augmented assign: dict key", t_aug_dict_key),
    ("augmented assign reads old value first, RHS once", t_aug_read_old_value_first),
    ("augmented assign: missing dict key", t_aug_missing_dict_key),
    ("augmented assign: out of range", t_aug_out_of_range_index),
    ("augmented assign: undefined name", t_aug_undefined_name),
    ("augmented assign: reserved names refused", t_aug_reserved_names),
    ("augmented assign: member write still refused", t_aug_member_write_still_refused),
    ("negative index: lists", t_negative_index_list),
    ("negative index: text", t_negative_index_text),
    ("negative index: friendly out-of-range", t_negative_out_of_range_message),
    ("negative index: assignment", t_negative_index_write),
    ("slice step: reverse", t_slice_reverse),
    ("slice step: positive", t_slice_step_positive),
    ("slice step: negative bounds", t_slice_negative_bounds),
    ("slice step: negative start", t_slice_step_negative_start),
    ("slice step: zero refused", t_slice_step_zero),
    ("slice parts: non-int refused", t_slice_non_int_parts),
    ("slice clamps still hold", t_slice_clamps_still_hold),
    ("slice full + plain forms", t_slice_full_and_plain),
    ("slice assignment: the v1.8 quirk stays", t_slice_assignment_quirk),
    ("insert: basics", t_insert_basic),
    ("insert: guards", t_insert_guards),
    ("remove_at: basics", t_remove_at_basic),
    ("remove_at: guards", t_remove_at_guards),
    ("clear: basics", t_clear_basic),
    ("clear: guards", t_clear_guards),
    ("extend: basics", t_extend_basic),
    ("extend: guards", t_extend_guards),
    ("unique: basics", t_unique_basic),
    ("unique: one equality", t_unique_uses_the_one_equality),
    ("unique: guards", t_unique_guards),
    ("delete: basics", t_delete_basic),
    ("delete: guards", t_delete_guards),
    ("items: basics", t_items_basic),
    ("items: guards", t_items_guards),
    ("merge: basics", t_merge_basic),
    ("merge: guards", t_merge_guards),
    ("index_of: basics", t_index_of_basic),
    ("index_of: guards", t_index_of_guards),
    ("starts_with / ends_with: basics", t_starts_ends_basic),
    ("starts_with / ends_with: guards", t_starts_ends_guards),
    ("ord/chr: a pair", t_ord_chr_pair),
    ("ord/chr: guards", t_ord_chr_guards),
    ("sets: display + dedupe", t_set_display_and_dedupe),
    ("sets: first-seen order", t_set_order_is_first_seen),
    ("sets: equality rules", t_set_equality_rules),
    ("sets: len / in / truthiness", t_set_len_membership_truthy),
    ("sets: for-in", t_set_for_in),
    ("sets: sorted is a new list", t_set_sorted_is_a_new_list),
    ("sets: type says set", t_set_type),
    ("sets: union / intersect / difference", t_set_ops),
    ("sets: ops guards", t_set_ops_guards),
    ("sets: + refused", t_set_plus_refused),
    ("sets: indexing refused", t_set_index_refused),
    ("sets: {} is still a dict", t_no_set_literal),
    ("\\u escape: works", t_unicode_escape_works),
    ("\\u escape: needs 4 hex digits", t_unicode_escape_needs_four_hex_digits),
    ("\\u escape: surrogates refused", t_unicode_escape_surrogates_refused),
    ("escape hint lists \\u", t_escape_hint_lists_u),
    ("registry tables agree", t_registry_tables_agree),
    ("min/max variadic", t_min_max_variadic),
    ("mirror rule for the new builtins", t_mirror_rule_for_the_new_builtins),
    ("grammar colors the language", t_grammar_colors_the_language),
    ("dump forms: aug + slice-step", t_dump_forms),
    ("dump forms: all five ops", t_dump_forms_all_five_ops),
    ("backward compat: plain programs", t_backward_compat_plain_programs),
    ("version 1.11 + keyword count", t_version_and_surface),
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
