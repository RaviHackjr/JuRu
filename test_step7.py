"""JuRu Step 7 tests — modules (import).

Rules under test:
- import "file.jr" → the module gets the file's stem as its name
- a module runs EXACTLY once per program (cached), even if imported twice
- a module is CHECKED before it runs (no unchecked code ever executes)
- a module sees nothing from the importer (isolation)
- import loops are caught with a human message
- the module name must be a valid JuRu name
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

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


def run_in(directory, src):
    """Run source with imports resolving against `directory`."""
    import contextlib
    tree = check_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(tree, base_dir=directory)
    return buf.getvalue()


def scratch(files):
    """A temp dir with the given {name: content} files. Returns its path."""
    d = tempfile.mkdtemp(prefix="juru_step7_")
    for name, content in files.items():
        target = os.path.join(d, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
    return d


def expect_galti_from(directory, src, fragment):
    try:
        run_in(directory, src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected an error, but the program ran")


import io  # noqa: E402  (used by run_in; kept here for clarity)


# ------------------------------------------------------------------ basics
def t_import_demo_exact():
    path = os.path.join(HERE, "examples", "test", "import_demo.jr")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    assert run_in(os.path.join(HERE, "examples", "test"), src) == (
        "hello JuRu!\n"
        "42\n"
        "magic number: 42\n"
        "100\n"
    )


def t_module_funcs_and_vars():
    d = scratch({"tools.jr": "func sq(n) {\n    return n * n\n}\ncolor = \"red\"\n"})
    out = run_in(d, 'import "tools.jr"\nsay(tools.sq(9))\nsay(tools.color)')
    assert out == "81\nred\n", out
    shutil.rmtree(d)


def t_module_runs_once():
    d = scratch({"once.jr": 'say("module loaded")\ntotal_seen = 7\n'})
    out = run_in(d, 'import "once.jr"\nimport "once.jr"\nsay(once.total_seen)')
    assert out == "module loaded\n7\n", out   # 'module loaded' printed exactly once
    shutil.rmtree(d)


def t_module_display():
    d = scratch({"m.jr": "x = 1\n"})
    out = run_in(d, 'import "m.jr"\nsay(m)')
    assert out == "<module m>\n", out
    shutil.rmtree(d)


def t_module_isolation():
    """A module cannot see the importer's variables."""
    d = scratch({
        "peek.jr": "say(secret)\n",       # secret lives only in the importer
    })
    expect_galti_from(
        d, 'secret = 99\nimport "peek.jr"',
        "in 'peek.jr': 'secret' was not found")
    shutil.rmtree(d)


def t_module_is_checked():
    """A module with a typo never runs — the checker speaks first."""
    d = scratch({
        "broken.jr": "func f() {\n    return ghsot\n}\n",   # typo
    })
    expect_galti_from(
        d, 'import "broken.jr"',
        "in 'broken.jr': 'ghsot' was not found")
    shutil.rmtree(d)


def t_module_member_missing():
    d = scratch({"lib.jr": "a = 1\nb = 2\n"})
    expect_galti_from(
        d, 'import "lib.jr"\nsay(lib.nope)',
        "'lib' has no 'nope' — the module has: a, b")
    expect_galti_from(
        d, 'import "empty.jr"' if False else 'import "lib.jr"\nsay(lib.zzz)',
        "'lib' has no 'zzz'")
    shutil.rmtree(d)


def t_module_chain():
    """A module may import another module."""
    d = scratch({
        "base.jr": "func base() {\n    return 10\n}\n",
        "mid.jr": 'import "base.jr"\nfunc mid() {\n    return base.base() + 5\n}\n',
    })
    out = run_in(d, 'import "mid.jr"\nsay(mid.mid())')
    assert out == "15\n", out
    shutil.rmtree(d)


def t_import_inside_func_is_local():
    """Import inside a func binds locally — gone after the call returns."""
    d = scratch({"m2.jr": "tag = \"local\"\n"})
    out = run_in(d, 'func load() {\n    import "m2.jr"\n    return m2.tag\n}\n'
                     'say(load())')
    assert out == "local\n", out
    shutil.rmtree(d)


# ------------------------------------------------------------------ errors
def t_import_missing_file():
    d = scratch({})
    expect_galti_from(
        d, 'import "nope.jr"',
        "cannot import 'nope.jr' — file not found")
    shutil.rmtree(d)


def t_import_loop_two_files():
    d = scratch({
        "a.jr": 'import "b.jr"\n',
        "b.jr": 'import "a.jr"\n',
    })
    expect_galti_from(
        d, 'import "a.jr"',
        "import loop: a.jr -> b.jr -> a.jr")
    shutil.rmtree(d)


def t_import_loop_self():
    d = scratch({"loop.jr": 'import "loop.jr"\n'})
    expect_galti_from(
        d, 'import "loop.jr"',
        "import loop: loop.jr -> loop.jr")
    shutil.rmtree(d)


def t_import_parse_errors():
    expect_galti_from(HERE, "import utils.jr", "import needs the file in double quotes")
    expect_galti_from(HERE, 'import "utils.py"', "JuRu files end with '.jr'")
    expect_galti_from(HERE, 'import "my-utils.jr"', "is not a valid name")
    expect_galti_from(HERE, 'import "import.jr"', "that is a keyword")


def t_subdir_import():
    d = scratch({"lib/deep.jr": "deep_value = 5\n"})
    out = run_in(d, 'import "lib/deep.jr"\nsay(deep.deep_value)')
    assert out == "5\n", out
    shutil.rmtree(d)


# ------------------------------------------------------------------ the real CLI
def t_cli_import_demo():
    proc = subprocess.run(
        [sys.executable, "juru.py", os.path.join("examples", "test", "import_demo.jr")],
        capture_output=True, text=True, cwd=HERE,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == (
        "hello JuRu!\n"
        "42\n"
        "magic number: 42\n"
        "100\n"
    ), proc.stdout


def t_cli_missing_import():
    path = os.path.join(HERE, ".tmp_imp.jr")
    with open(path, "w", encoding="utf-8") as f:
        f.write('import "ghost_file.jr"\n')
    try:
        proc = subprocess.run(
            [sys.executable, "juru.py", path], capture_output=True, text=True, cwd=HERE)
        assert proc.returncode == 1
        assert "cannot import 'ghost_file.jr' — file not found" in proc.stdout, proc.stdout
    finally:
        os.remove(path)


def t_module_name_builtin_refused():
    """import "len.jr" would create a module named len — reserved, refused."""
    d = scratch({"len.jr": "x = 1\n"})
    try:
        check_source('import "len.jr"')
        raise AssertionError("checker allowed a builtin module name")
    except JuRuGalti as err:
        assert "reserved builtin" in err.message, err.message
    try:
        run_in(d, 'import "len.jr"')
        raise AssertionError("runtime allowed a builtin module name")
    except JuRuGalti as err:
        assert "reserved builtin" in err.message, err.message
    shutil.rmtree(d)


ALL = [
    ("import_demo exact output", t_import_demo_exact),
    ("module funcs + vars", t_module_funcs_and_vars),
    ("module runs exactly once", t_module_runs_once),
    ("module display", t_module_display),
    ("module isolation", t_module_isolation),
    ("module is checked before running", t_module_is_checked),
    ("module member missing", t_module_member_missing),
    ("module imports another module", t_module_chain),
    ("import inside a func is local", t_import_inside_func_is_local),
    ("import missing file", t_import_missing_file),
    ("import loop (two files)", t_import_loop_two_files),
    ("import loop (self)", t_import_loop_self),
    ("import parse errors", t_import_parse_errors),
    ("import from a subfolder", t_subdir_import),
    ("module name cannot be a builtin", t_module_name_builtin_refused),
    ("CLI: import_demo.jr", t_cli_import_demo),
    ("CLI: missing import", t_cli_missing_import),
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
