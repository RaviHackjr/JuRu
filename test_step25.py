r"""JuRu Step 25 tests — files & JSON (zero new keywords).

Thirteen new reserved builtins (54 → 67): read_file, write_file,
append_file, read_lines, write_lines, file_exists, file_size,
delete_file, list_dir, make_dir, delete_dir, to_json, from_json.

Every behavior the roadmap left open is decided here and pinned:

  - paths: relative paths resolve against the PROGRAM's directory (the
    same rule imports use), absolute paths are used as they are, "~" is
    NOT expanded, ".." is not refused (an honest, size-guarded tool).
  - files: UTF-8 only, 10 MB cap on every read/write/append/JSON text,
    missing files and folders / permission problems / bad UTF-8 are
    friendly errors with kind "file" — try/rescue can catch them.
  - lines: exactly split_lines()'s rules; write_lines() adds the final
    newline so read_lines(write_lines(xs)) == xs; [] writes an empty
    file; an embedded newline in one line is refused.
  - directories: list_dir() returns SORTED names; make_dir() creates
    parents and is idempotent; delete_dir() removes EMPTY folders only
    (never recursive); delete_file() refuses folders.
  - JSON: null/bool/int/float/text/list/dict(text keys) only; NaN and
    Infinity refused both ways (JSON has neither); cycles and nesting
    deeper than 64 levels refused; duplicate JSON keys keep the LAST
    value; unicode escapes (including surrogate pairs) decode; floats
    keep Python's shortest-repr JSON display, pinned below.
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import JuRuGalti, KEYWORDS
from juru.checker import check_source, BUILTINS, BUILTIN_ARITY, BUILTIN_HINT
from juru.parser import parse_source
from juru.interpreter import Interpreter
from juru.version import VERSION

HERE = os.path.dirname(os.path.abspath(__file__))
JURU = os.path.join(HERE, "juru.py")
RESULTS = []
NEW = ("read_file", "write_file", "append_file", "read_lines", "write_lines",
       "file_exists", "file_size", "delete_file", "list_dir", "make_dir",
       "delete_dir", "to_json", "from_json")
MAX = 10 * 1024 * 1024


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


# ------------------------------------------------------------------ helpers
@contextlib.contextmanager
def workspace():
    d = tempfile.mkdtemp(prefix="juru_s25_")
    try:
        yield d
    finally:
        for root, dirs, files in os.walk(d):
            os.chmod(root, 0o700)
            for name in files:
                try:
                    os.chmod(os.path.join(root, name), 0o600)
                except OSError:
                    pass
        shutil.rmtree(d, ignore_errors=True)


def run_in(src, base):
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=base)
    return buf.getvalue()


def galti_in(src, base):
    try:
        run_in(src, base)
    except JuRuGalti as err:
        return err
    raise AssertionError("expected a JuRu error: " + src)


def expect_galti(src, base, fragment, kind=None):
    err = galti_in(src, base)
    assert fragment in err.message, "{} -> {}".format(src, err.message)
    if kind is not None:
        assert err.kind == kind, "{} -> {} (kind {})".format(
            src, err.message, err.kind)
    return err


def quoted(text):
    """A JuRu text literal for text (JSON escapes match JuRu's)."""
    return json.dumps(text)


# ------------------------------------------------------------------ files: happy paths
def t_read_write_round_trip():
    with workspace() as d:
        assert run_in('write_file("a.txt", "héllo は")', d) == ""
        assert run_in('say(read_file("a.txt"))', d) == "héllo は\n"
        with open(os.path.join(d, "a.txt"), "rb") as f:
            assert f.read() == "héllo は".encode("utf-8")


def t_write_overwrites_and_appends():
    with workspace() as d:
        run_in('write_file("log.txt", "one")', d)
        assert run_in('say(read_file("log.txt"))', d) == "one\n"
        run_in('write_file("log.txt", "two")', d)
        assert run_in('say(read_file("log.txt"))', d) == "two\n"
        run_in('append_file("log.txt", "!")', d)
        assert run_in('say(read_file("log.txt"))', d) == "two!\n"


def t_append_creates_file():
    with workspace() as d:
        assert not os.path.exists(os.path.join(d, "new.txt"))
        run_in('append_file("new.txt", "a")', d)
        run_in('append_file("new.txt", "bは")', d)
        assert run_in('say(read_file("new.txt"))', d) == "abは\n"


def t_mutators_return_null():
    with workspace() as d:
        src = ('say(type(write_file("x.txt", "a")))\n'
               'say(type(append_file("x.txt", "b")))\n'
               'say(type(write_lines("l.txt", ["c"])))\n'
               'say(type(make_dir("sub")))\n'
               'say(type(delete_file("x.txt")))\n'
               'say(type(delete_dir("sub")))\n')
        assert run_in(src, d) == "null\n" * 6


# ------------------------------------------------------------------ files: errors + caps
def t_read_missing_file_is_file_error():
    with workspace() as d:
        err = expect_galti('say(read_file("missing.txt"))', d,
                           "file not found", kind="file")
        assert err.line == 1
        assert "read_file() could not read 'missing.txt'" in err.message
        assert os.path.join(d, "missing.txt") in err.message


def t_read_folder_is_refused():
    with workspace() as d:
        os.mkdir(os.path.join(d, "docs"))
        expect_galti('say(read_file("docs"))', d,
                     "it is a folder, not a file", kind="file")


def t_read_invalid_utf8():
    with workspace() as d:
        path = os.path.join(d, "raw.bin")
        with open(path, "wb") as f:
            f.write(b"\xff\xfeabc")
        expect_galti('say(read_file("raw.bin"))', d,
                     "the file is not valid UTF-8 text", kind="file")


def t_read_size_cap():
    with workspace() as d:
        with open(os.path.join(d, "big.txt"), "wb") as f:
            f.write(b"a" * (MAX + 1))
        expect_galti('say(read_file("big.txt"))', d,
                     "the file is too big", kind="file")


def t_write_guards():
    with workspace() as d:
        expect_galti('write_file("x.txt", 5)', d,
                     "needs text to write — got: 5", kind="type")
        expect_galti('append_file("x.txt", true)', d,
                     "needs text to append — got: true", kind="type")
        expect_galti('write_file("no/f.txt", "x")', d,
                     "the folder does not exist", kind="file")
        os.mkdir(os.path.join(d, "docs"))
        expect_galti('write_file("docs", "x")', d,
                     "it is a folder, not a file", kind="file")


def t_write_size_cap():
    with workspace() as d:
        # A JuRu text may hold 10,000,000 characters, but 3.6M wide chars
        # are 10.8 MB of UTF-8 — over the file cap even under the text cap.
        src = 'write_file("big.txt", "は" * 3600000)'
        expect_galti(src, d, "the text is too big", kind="file")


def t_append_size_cap():
    with workspace() as d:
        with open(os.path.join(d, "big.txt"), "wb") as f:
            f.write(b"a" * MAX)
        expect_galti('append_file("big.txt", "x")', d,
                     "the file would become too big", kind="file")


# ------------------------------------------------------------------ paths
def t_relative_paths_resolve_to_program_dir():
    with workspace() as d:
        run_in('write_file("notes.txt", "here")', d)
        assert os.path.isfile(os.path.join(d, "notes.txt"))
        # cwd is irrelevant; the value came from the program directory
        assert run_in('say(read_file("notes.txt"))', d) == "here\n"


def t_absolute_and_relative_paths():
    with workspace() as d:
        target = os.path.join(d, "abs.txt")
        run_in("write_file({}, \"absolute\")".format(quoted(target)), d)
        assert open(target, encoding="utf-8").read() == "absolute"
        assert run_in("say(read_file({}))".format(quoted(target)), d) == "absolute\n"


def t_no_home_expansion():
    with workspace() as d:
        assert run_in('say(file_exists("~/juru-no-such-file"))', d) == "false\n"
        run_in('make_dir("~")', d)
        assert os.path.isdir(os.path.join(d, "~"))
        assert run_in('say(file_exists("~"))', d) == "true\n"


def t_dotdot_allowed():
    with workspace() as d:
        run_in('make_dir("sub")', d)
        run_in('write_file("sub/../up.txt", "up")', d)
        assert open(os.path.join(d, "up.txt"), encoding="utf-8").read() == "up"


def t_empty_path_guard():
    with workspace() as d:
        expect_galti('read_file("")', d,
                     "it cannot be empty", kind="value")
        expect_galti('file_exists("")', d,
                     "it cannot be empty", kind="value")
        expect_galti('read_file(5)', d,
                     "needs a file path in text — got: 5", kind="type")


# ------------------------------------------------------------------ lines
def t_read_lines_unicode_and_blanks():
    with workspace() as d:
        run_in('write_file("l.txt", "a\\nは\\n\\nz\\n")', d)
        assert run_in('say(read_lines("l.txt"))', d) == "[a, は, , z]\n"
        assert run_in('say(len(read_lines("l.txt")))', d) == "4\n"


def t_read_lines_line_endings():
    with workspace() as d:
        with open(os.path.join(d, "crlf.txt"), "wb") as f:
            f.write(b"a\r\nb\rc\nd")
        assert run_in('say(read_lines("crlf.txt"))', d) == "[a, b, c, d]\n"


def t_read_lines_empty_and_trailing():
    with workspace() as d:
        open(os.path.join(d, "empty.txt"), "wb").close()
        assert run_in('say(read_lines("empty.txt"))', d) == "[]\n"
        # A file holding one newline is ONE empty line, exactly like
        # split_lines("\n") == [""] — say() cannot show the difference.
        run_in('write_file("one.txt", "\\n")', d)
        assert run_in('say(len(read_lines("one.txt")))', d) == "1\n"
        assert run_in('say(read_lines("one.txt") == [""])', d) == "true\n"
        run_in('write_file("two.txt", "a\\n\\n")', d)
        assert run_in('say(read_lines("two.txt") == ["a", ""])', d) == "true\n"


def t_write_lines_round_trip():
    with workspace() as d:
        src = 'write_lines("todo.txt", ["milk", "", "は"])'
        run_in(src, d)
        with open(os.path.join(d, "todo.txt"), "rb") as f:
            assert f.read() == b"milk\n\n\xe3\x81\xaf\n"
        assert run_in('say(read_lines("todo.txt"))', d) == "[milk, , は]\n"


def t_write_lines_empty_and_guards():
    with workspace() as d:
        run_in('write_lines("empty.txt", [])', d)
        assert os.path.getsize(os.path.join(d, "empty.txt")) == 0
        assert run_in('say(read_lines("empty.txt"))', d) == "[]\n"
        expect_galti('write_lines("x.txt", "nope")', d,
                     "needs a list of lines — got: nope", kind="type")
        expect_galti('write_lines("x.txt", ["a", 2])', d,
                     "needs every line to be text — got: 2 at position 2",
                     kind="type")
        expect_galti('write_lines("x.txt", ["a\\nb"])', d,
                     "needs each line to be ONE line — line 1 contains a newline",
                     kind="value")
        expect_galti('write_lines("x.txt", ["a" + chr(13) + "b"])', d,
                     "line 1 contains a newline", kind="value")


# ------------------------------------------------------------------ existence + size
def t_file_exists_semantics():
    with workspace() as d:
        assert run_in('say(file_exists("no.txt"))', d) == "false\n"
        run_in('write_file("yes.txt", "x")', d)
        assert run_in('say(file_exists("yes.txt"))', d) == "true\n"
        run_in('make_dir("docs")', d)
        assert run_in('say(file_exists("docs"))', d) == "true\n"
        run_in('delete_file("yes.txt")', d)
        assert run_in('say(file_exists("yes.txt"))', d) == "false\n"


def t_file_size_bytes_and_guards():
    with workspace() as d:
        run_in('write_file("ascii.txt", "abc")', d)
        run_in('write_file("wide.txt", "は")', d)
        run_in('write_file("accent.txt", "é")', d)
        assert run_in('say(file_size("ascii.txt"))', d) == "3\n"
        assert run_in('say(file_size("wide.txt"))', d) == "3\n"   # bytes, not characters
        assert run_in('say(file_size("accent.txt"))', d) == "2\n"
        run_in('make_dir("docs")', d)
        expect_galti('file_size("docs")', d,
                     "file_size() needs a file — 'docs' is a folder",
                     kind="file")
        expect_galti('file_size("no.txt")', d,
                     "file not found", kind="file")


# ------------------------------------------------------------------ delete file
def t_delete_file_semantics():
    with workspace() as d:
        run_in('write_file("gone.txt", "x")', d)
        run_in('delete_file("gone.txt")', d)
        assert not os.path.exists(os.path.join(d, "gone.txt"))
        expect_galti('delete_file("gone.txt")', d,
                     "file not found", kind="file")
        run_in('make_dir("docs")', d)
        expect_galti('delete_file("docs")', d,
                     "refuses a folder", kind="file")
        assert os.path.isdir(os.path.join(d, "docs"))


# ------------------------------------------------------------------ directories
def t_list_dir_sorted():
    with workspace() as d:
        for name in ("b.txt", "a.txt", "c.txt"):
            run_in('write_file({}, "x")'.format(quoted(name)), d)
        run_in('make_dir("zz")', d)
        assert run_in('say(list_dir("."))', d) == "[a.txt, b.txt, c.txt, zz]\n"


def t_list_dir_empty_and_guards():
    with workspace() as d:
        run_in('make_dir("empty")', d)
        assert run_in('say(list_dir("empty"))', d) == "[]\n"
        run_in('write_file("file.txt", "x")', d)
        expect_galti('list_dir("file.txt")', d,
                     "needs a folder", kind="file")
        expect_galti('list_dir("missing")', d,
                     "folder not found", kind="file")


def t_make_dir_parents_and_idempotent():
    with workspace() as d:
        run_in('make_dir("a/b/c")', d)
        assert os.path.isdir(os.path.join(d, "a", "b", "c"))
        run_in('make_dir("a/b/c")', d)          # already there: no error
        run_in('write_file("a/b/c/ok.txt", "x")', d)
        assert os.path.isfile(os.path.join(d, "a", "b", "c", "ok.txt"))


def t_make_dir_conflict():
    with workspace() as d:
        run_in('write_file("taken", "x")', d)
        expect_galti('make_dir("taken")', d,
                     "a file with that name already exists", kind="file")


def t_delete_dir_empty_only():
    with workspace() as d:
        run_in('make_dir("empty")', d)
        run_in('delete_dir("empty")', d)
        assert not os.path.exists(os.path.join(d, "empty"))
        run_in('make_dir("full")', d)
        run_in('write_file("full/x.txt", "x")', d)
        expect_galti('delete_dir("full")', d,
                     "only removes an EMPTY folder", kind="file")
        assert os.path.isdir(os.path.join(d, "full"))


def t_delete_dir_guards():
    with workspace() as d:
        expect_galti('delete_dir("missing")', d,
                     "folder not found", kind="file")
        run_in('write_file("file.txt", "x")', d)
        expect_galti('delete_dir("file.txt")', d,
                     "needs a folder", kind="file")


# ------------------------------------------------------------------ JSON: to_json
def t_to_json_scalars():
    with workspace() as d:
        assert run_in('say(to_json(null))', d) == "null\n"
        assert run_in('say(to_json(true))', d) == "true\n"
        assert run_in('say(to_json(false))', d) == "false\n"
        assert run_in('say(to_json(42))', d) == "42\n"
        assert run_in('say(to_json(1.5))', d) == "1.5\n"
        assert run_in('say(to_json("hi"))', d) == "\"hi\"\n"


def t_to_json_containers():
    with workspace() as d:
        assert run_in('say(to_json([1, true, null, "x"]))', d) == \
            "[1, true, null, \"x\"]\n"
        assert run_in('say(to_json({"b": 2, "a": [1, {"c": "は"}]}))', d) == \
            "{\"b\": 2, \"a\": [1, {\"c\": \"は\"}]}\n"
        assert run_in('say(to_json({}))', d) == "{}\n"
        assert run_in('say(to_json([]))', d) == "[]\n"


def t_to_json_unicode_and_float_display():
    with workspace() as d:
        assert run_in('say(to_json("は"))', d) == "\"は\"\n"   # no \\u escaping
        assert run_in('say(to_json("😀"))', d) == "\"😀\"\n"
        # Python's shortest-repr JSON float display, pinned exactly
        assert run_in('say(to_json(1.0))', d) == "1.0\n"
        assert run_in('say(to_json(0.1 + 0.2))', d) == "0.30000000000000004\n"
        assert run_in('say(to_json(float("1e20")))', d) == "1e+20\n"
        assert run_in('say(to_json(float("1e-7")))', d) == "1e-07\n"
        assert run_in('say(to_json(123456789.0))', d) == "123456789.0\n"


def t_to_json_type_guards():
    with workspace() as d:
        expect_galti('to_json({1: "x"})', d,
                     "needs text keys in every dict — found 1", kind="type")
        expect_galti('to_json(set_of([1, 2]))', d,
                     "cannot write a set", kind="type")
        expect_galti("func f() { return 1 }\nto_json(f)", d,
                     "cannot write a func", kind="type")


def t_to_json_nonfinite_and_cycles():
    with workspace() as d:
        expect_galti('to_json(float("nan"))', d,
                     "cannot write a number that is not finite", kind="value")
        expect_galti('to_json(float("inf"))', d,
                     "JSON has no NaN or Infinity", kind="value")
        expect_galti('a = []\npush(a, a)\nto_json(a)', d,
                     "contains itself", kind="value")
        expect_galti('d = {}\nd["self"] = d\nto_json(d)', d,
                     "contains itself", kind="value")


def t_to_json_depth_and_size_caps():
    with workspace() as d:
        ok = ('v = 1\nfor i from 1 to 64 { v = [v] }\n'
              'say(len(to_json(v)) > 0)\n')
        assert run_in(ok, d) == "true\n"
        deep = ('v = 1\nfor i from 1 to 65 { v = [v] }\nto_json(v)')
        expect_galti(deep, d, "nested too deeply — the limit is 64 levels",
                     kind="value")
        too_big = 'to_json("は" * 3600000)'
        expect_galti(too_big, d, "produced too much text", kind="value")


# ------------------------------------------------------------------ JSON: from_json
def t_from_json_basics():
    with workspace() as d:
        assert run_in('say(from_json("null"))', d) == "null\n"
        assert run_in('say(from_json("true"))', d) == "true\n"
        assert run_in('say(from_json("42"))', d) == "42\n"
        assert run_in('say(from_json("1.5"))', d) == "1.5\n"
        assert run_in('say(from_json("\\"hi\\""))', d) == "hi\n"
        assert run_in('say(type(from_json("1")))', d) == "int\n"
        assert run_in('say(type(from_json("1.0")))', d) == "float\n"
        assert run_in('say(from_json("[]"))', d) == "[]\n"
        assert run_in('say(from_json("{}"))', d) == "{}\n"
        assert run_in('say(from_json("{\\"a\\": [1, null]}"))', d) == \
            "{a: [1, null]}\n"


def t_from_json_unicode_escapes():
    with workspace() as d:
        assert run_in(r'say(from_json("\"\\u0041\\u00e9\""))', d) == "Aé\n"
        assert run_in(r'say(from_json("\"\\ud83d\\ude00\""))', d) == "😀\n"
        assert run_in('say(from_json("\\"は\\""))', d) == "は\n"


def t_from_json_duplicate_key_last_wins():
    with workspace() as d:
        assert run_in('say(from_json("{\\"a\\": 1, \\"a\\": 2}")["a"])', d) == "2\n"


def t_from_json_bad_text():
    with workspace() as d:
        expect_galti('from_json("")', d,
                     "could not read the text", kind="value")
        expect_galti('from_json("{bad}")', d,
                     "expecting property name enclosed in double quotes",
                     kind="value")
        expect_galti('from_json("1 2")', d, "extra data", kind="value")
        expect_galti('from_json("\\"unterminated")', d,
                     "unterminated string", kind="value")


def t_from_json_nonfinite():
    with workspace() as d:
        for bad in ("NaN", "Infinity", "-Infinity"):
            expect_galti('from_json("{}")'.format(bad), d,
                         "cannot read NaN or Infinity", kind="value")
        # A syntactically valid JSON number that overflows Python's float
        # becomes inf — JSON has no Infinity, so it is refused too.
        for bad in ("1e400", "-1e400"):
            expect_galti('from_json("{}")'.format(bad), d,
                         "cannot read NaN or Infinity", kind="value")


def t_from_json_lone_surrogate():
    with workspace() as d:
        bad_texts = ['"\\ud800"', '"\\udc00"', '{"\\ud800": 1}', '["\\udfff"]']
        for text in bad_texts:
            expect_galti("from_json({})".format(quoted(text)), d,
                         "unpaired surrogate escape", kind="value")


def t_path_nul_guard():
    with workspace() as d:
        for call in ('read_file("a\\u0000b")',
                     'write_file("a\\u0000b", "x")',
                     'make_dir("a\\u0000b")'):
            expect_galti(call, d, "without NUL characters", kind="value")


def t_from_json_depth_and_size_caps():
    with workspace() as d:
        text64 = "[" * 64 + "1" + "]" * 64
        assert run_in('say(type(from_json("{}")))'.format(text64), d) == "list\n"
        text65 = "[" * 65 + "1" + "]" * 65
        expect_galti('from_json("{}")'.format(text65), d,
                     "nested too deeply — the limit is 64 levels", kind="value")
        expect_galti('from_json("は" * 3600000)', d,
                     "text is too big", kind="value")


def t_from_json_type_guard():
    with workspace() as d:
        expect_galti("from_json(5)", d,
                     "needs JSON text — got: 5", kind="type")


# ------------------------------------------------------------------ JSON + files together
def t_json_file_round_trip():
    with workspace() as d:
        src = ('data = {"name": "Ravi", "scores": [10, 20.5], '
               '"ok": true, "none": null, "は": "é"}\n'
               'write_file("data.json", to_json(data))\n'
               'back = from_json(read_file("data.json"))\n'
               'say(back["name"])\n'
               'say(back["scores"][1])\n'
               'say(back["ok"])\n'
               'say(back["none"])\n'
               'say(back["は"])\n')
        assert run_in(src, d) == "Ravi\n20.5\ntrue\nnull\né\n"


def t_file_errors_are_catchable():
    with workspace() as d:
        src = ('try { read_file("missing.txt") } rescue as e '
               '{ say(e.kind + ":" + e.message) }\n'
               'try { write_file("missing/child.txt", "x") } rescue as e '
               '{ say(e.kind) }\n'
               'try { delete_file("missing.txt") } rescue as e '
               '{ say(e.kind) }\n')
        out = run_in(src, d)
        lines = out.splitlines()
        assert lines[0].startswith("file:read_file() could not read"), out
        assert lines[1] == "file", out
        assert lines[2] == "file", out


# ------------------------------------------------------------------ permissions
def t_permission_error_is_friendly():
    if not hasattr(os, "geteuid") or os.geteuid() == 0:
        return                                   # root ignores file modes
    with workspace() as d:
        path = os.path.join(d, "locked.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("secret")
        os.chmod(path, 0)
        try:
            err = galti_in('say(read_file("locked.txt"))', d)
            assert err.kind == "file", err.kind
            assert "could not read 'locked.txt'" in err.message
            assert ("denied" in err.message or "permission" in err.message.lower()), \
                err.message
        finally:
            os.chmod(path, 0o600)


# ------------------------------------------------------------------ CLI path rule
def t_cli_resolves_program_directory():
    with workspace() as d:
        name = "step25_cli_out.txt"
        script = os.path.join(d, "writer.jr")
        with open(script, "w", encoding="utf-8") as f:
            f.write('write_file({}, "from-cli")\n'
                    'say(read_file({}))\n'.format(quoted(name), quoted(name)))
        stray = os.path.join(HERE, name)
        if os.path.exists(stray):
            os.remove(stray)
        proc = subprocess.run(
            [sys.executable, JURU, script],
            capture_output=True, text=True, cwd=HERE, timeout=60,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout == "from-cli\n", proc.stdout
        with open(os.path.join(d, name), encoding="utf-8") as f:
            assert f.read() == "from-cli"
        assert not os.path.exists(stray), "resolved against cwd, not the program"


# ------------------------------------------------------------------ registry + docs
def t_registry_and_surface():
    assert VERSION == "1.12"
    assert len(KEYWORDS) == 21                       # zero new keywords
    assert len(BUILTINS) == 67                       # 54 + the 13 file/JSON tools
    assert set(NEW) <= set(BUILTINS)
    assert BUILTIN_ARITY["read_file"] == (1, 1)
    assert BUILTIN_ARITY["write_file"] == (2, 2)
    assert BUILTIN_ARITY["append_file"] == (2, 2)
    assert BUILTIN_ARITY["write_lines"] == (2, 2)
    for name in NEW:
        assert BUILTIN_HINT[name], name
        assert name in BUILTIN_HINT[name], name
    from juru import helpdb
    assert set(helpdb.BUILTIN_CARDS) == set(BUILTINS)
    assert len(helpdb.BUILTIN_CARDS) == 67
    assert len(helpdb.KEYWORD_CARDS) == 21


def t_help_group_and_cards():
    from juru import helpdb
    text = helpdb.overview()
    assert "21 keywords + 67 builtins" in text
    assert "files + json:" in text
    for name in NEW:
        assert name in text, "overview misses " + name
        card = helpdb.card_for(name)
        assert card is not None, name
        assert name + "(" in card, name
    assert "10 MB" in helpdb.card_for("read_file")
    assert "EMPTY folder" in helpdb.card_for("delete_dir")
    assert "LAST value" in helpdb.card_for("from_json")
    assert "ONE line" in helpdb.card_for("write_lines")


def t_old_builtins_unchanged():
    with workspace() as d:
        assert run_in('say(format("{} {}", "a", 1))', d) == "a 1\n"
        assert run_in('say(split_lines("a\\nb"))', d) == "[a, b]\n"
        assert run_in('say(join_lines(["a", "b"]))', d) == "a\nb\n"
        assert run_in('say(file_exists("nope"))', d) == "false\n"


def t_no_parser_changes():
    # these are plain calls — the AST is the ordinary Call node, nothing new
    tree = parse_source('x = read_file("y")')
    assign = tree.stmts[0]
    assert type(assign).__name__ == "Assign"
    assert type(assign.value).__name__ == "Call"
    assert check_source('say(to_json([1]))') is not None


ALL = [
    ("files: write → read round-trip (unicode)", t_read_write_round_trip),
    ("files: overwrite + append", t_write_overwrites_and_appends),
    ("files: append creates the file", t_append_creates_file),
    ("files: writers return null", t_mutators_return_null),
    ("read: missing file is a kind-file error", t_read_missing_file_is_file_error),
    ("read: a folder is refused", t_read_folder_is_refused),
    ("read: invalid UTF-8 is friendly", t_read_invalid_utf8),
    ("read: 10 MB cap", t_read_size_cap),
    ("write: type / folder guards", t_write_guards),
    ("write: 10 MB cap", t_write_size_cap),
    ("append: resulting-size cap", t_append_size_cap),
    ("paths: relative to the program directory", t_relative_paths_resolve_to_program_dir),
    ("paths: absolute and relative both work", t_absolute_and_relative_paths),
    ("paths: no ~ expansion", t_no_home_expansion),
    ("paths: .. is not refused", t_dotdot_allowed),
    ("paths: empty and non-text guards", t_empty_path_guard),
    ("read_lines: unicode + blank lines", t_read_lines_unicode_and_blanks),
    ("read_lines: LF, CRLF, lone CR", t_read_lines_line_endings),
    ("read_lines: empty + trailing newline", t_read_lines_empty_and_trailing),
    ("write_lines: round-trip + final newline", t_write_lines_round_trip),
    ("write_lines: empty list + guards", t_write_lines_empty_and_guards),
    ("file_exists: file / folder / missing", t_file_exists_semantics),
    ("file_size: bytes + guards", t_file_size_bytes_and_guards),
    ("delete_file: removes, missing, folder", t_delete_file_semantics),
    ("list_dir: sorted names", t_list_dir_sorted),
    ("list_dir: empty + guards", t_list_dir_empty_and_guards),
    ("make_dir: parents + idempotent", t_make_dir_parents_and_idempotent),
    ("make_dir: file conflict", t_make_dir_conflict),
    ("delete_dir: empty only, never recursive", t_delete_dir_empty_only),
    ("delete_dir: missing / file guards", t_delete_dir_guards),
    ("to_json: scalars", t_to_json_scalars),
    ("to_json: containers", t_to_json_containers),
    ("to_json: unicode + float display pinned", t_to_json_unicode_and_float_display),
    ("to_json: func / set / int-key guards", t_to_json_type_guards),
    ("to_json: NaN/Infinity + cycles", t_to_json_nonfinite_and_cycles),
    ("to_json: depth + size caps", t_to_json_depth_and_size_caps),
    ("from_json: basics + int/float shape", t_from_json_basics),
    ("from_json: unicode escapes + surrogates", t_from_json_unicode_escapes),
    ("from_json: duplicate key → last wins", t_from_json_duplicate_key_last_wins),
    ("from_json: bad text is friendly", t_from_json_bad_text),
    ("from_json: NaN/Infinity refused", t_from_json_nonfinite),
    ("from_json: lone surrogate escapes refused", t_from_json_lone_surrogate),
    ("paths: NUL characters refused", t_path_nul_guard),
    ("from_json: depth + size caps", t_from_json_depth_and_size_caps),
    ("from_json: non-text guard", t_from_json_type_guard),
    ("JSON + files: write → read → from_json", t_json_file_round_trip),
    ("file errors are catchable (kind file)", t_file_errors_are_catchable),
    ("permission errors are friendly", t_permission_error_is_friendly),
    ("CLI: paths resolve next to the program", t_cli_resolves_program_directory),
    ("registry: 67 builtins, cards, 21 keywords", t_registry_and_surface),
    ("help: files + json group and cards", t_help_group_and_cards),
    ("old builtins unchanged", t_old_builtins_unchanged),
    ("no parser changes needed", t_no_parser_changes),
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
