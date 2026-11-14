"""JuRu Step 13/14 tests — the package is real and the editor bits are valid.

What is enforced here:
  - pyproject.toml parses, names the package, wires the `juru` script, and
    takes its version from juru/version.py (one source of truth)
  - the src/juru package imports cleanly on its own (no stray root imports)
  - a REAL wheel is built, installed into a fresh venv, and the installed
    `juru` command runs programs, templates and the REPL
  - the wheel actually ships the templates
  - the VS Code extension files are valid JSON, and the grammar's keyword
    list matches the language's KEYWORDS exactly (docs cannot drift)

The venv part needs pip; when pip is missing the test says SKIP instead of
pretending to pass (the structural tests always run).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import KEYWORDS
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


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 240)
    return subprocess.run(cmd, **kw)


# ------------------------------------------------------------------ pyproject
def t_pyproject_is_sound():
    with open(os.path.join(HERE, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["name"] == "juru"
    assert data["project"]["scripts"] == {"juru": "juru.cli:main"}
    assert data["project"]["requires-python"] == ">=3.8"
    assert "version" not in data["project"], "version must be dynamic (one source of truth)"
    assert data["tool"]["setuptools"]["package-dir"] == {"" : "src"}
    assert data["tool"]["setuptools"]["packages"] == ["juru"]
    assert data["tool"]["setuptools"]["package-data"]["juru"] == ["templates/*.jr"]
    assert data["tool"]["setuptools"]["dynamic"]["version"]["attr"] == "juru.version.VERSION"


def t_pyproject_version_is_the_only_truth():
    from juru.version import VERSION as v
    assert v == VERSION
    with open(os.path.join(HERE, "pyproject.toml"), "rb") as f:
        text = f.read().decode()
    assert "dynamic = [\"version\"]" in text
    assert 'attr = "juru.version.VERSION"' in text


def t_package_imports_cleanly():
    """From a foreign cwd, with only src on the path: every module imports."""
    code = (
        "import juru, juru.lexer, juru.parser, juru.checker, "
        "juru.interpreter, juru.cli, juru.repl; print(juru.VERSION)"
    )
    proc = run([sys.executable, "-c", code], cwd="/", env={
        **os.environ, "PYTHONPATH": os.path.join(HERE, "src"),
    })
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == VERSION, proc.stdout


def t_root_launchers_work():
    for script, args, want in (
        ("juru.py", ["--version"], "JuRu " + VERSION),
        ("repl.py", [], "JuRu " + VERSION + " REPL"),
        ("checker.py", ["src/juru/templates/starter.jr"], "OK"),
    ):
        proc = run([sys.executable, os.path.join(HERE, script)] + args,
                   input="exit\n", cwd=HERE)
        assert proc.returncode == 0, (script, proc.stdout + proc.stderr)
        assert want in proc.stdout, (script, proc.stdout)
        assert "Traceback" not in proc.stderr, (script, proc.stderr)


def t_cli_repl_subcommand():
    """python3 juru.py repl opens the same REPL as python3 repl.py."""
    proc = run([sys.executable, os.path.join(HERE, "juru.py"), "repl"],
               input="say(2 + 3)\nexit\n", cwd=HERE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "JuRu " + VERSION + " REPL" in proc.stdout
    assert "jruru> 5" in proc.stdout, proc.stdout


# ------------------------------------------------------------------ the real wheel
def _pip_available():
    d = tempfile.mkdtemp(prefix="juru_pip_")
    proc = run([sys.executable, "-m", "venv", d + "/probe"])
    if proc.returncode != 0:
        return False
    proc = run([d + "/probe/bin/python", "-m", "pip", "--version"])
    shutil.rmtree(d, ignore_errors=True)
    return proc.returncode == 0


def t_wheel_builds_installs_and_runs():
    if not _pip_available():
        print("SKIP  (no pip available in this environment)")
        return
    work = tempfile.mkdtemp(prefix="juru_pkg_")
    try:
        # 1) a builder venv with setuptools, then a real wheel
        builder = os.path.join(work, "builder")
        assert run([sys.executable, "-m", "venv", builder]).returncode == 0
        proc = run([builder + "/bin/python", "-m", "pip", "install", "-q", "setuptools"])
        assert proc.returncode == 0, proc.stderr
        dist = os.path.join(work, "dist")
        proc = run([builder + "/bin/python", "-m", "pip", "wheel", HERE,
                    "--no-deps", "--no-build-isolation", "-w", dist])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        wheels = [n for n in os.listdir(dist) if n.endswith(".whl")]
        assert len(wheels) == 1 and wheels[0].startswith(
            "juru-{}-".format(VERSION)), wheels

        # 2) the wheel ships the templates
        with zipfile.ZipFile(os.path.join(dist, wheels[0])) as z:
            names = z.namelist()
        shipped = [n for n in names if n.startswith("juru/templates/")]
        assert len(shipped) == 5, shipped

        # 3) install into a FRESH venv (no network: the wheel has no deps)
        venv = os.path.join(work, "site")
        assert run([sys.executable, "-m", "venv", venv]).returncode == 0
        proc = run([venv + "/bin/pip", "install", "-q", "--no-index",
                    os.path.join(dist, wheels[0])])
        assert proc.returncode == 0, proc.stdout + proc.stderr

        # 4) the installed command is the whole language
        juru = venv + "/bin/juru"
        assert os.path.exists(juru), "the juru script was not installed"
        proc = run([juru, "--version"])
        assert proc.returncode == 0 and proc.stdout.strip() == "JuRu " + VERSION, proc.stdout
        proc = run([juru, "--templates"])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        for name in ("starter", "calculator", "quiz", "guessing_game", "word_stats"):
            assert name in proc.stdout, name

        # 5) --new + run a created program, from a foreign cwd
        sandbox = os.path.join(work, "sandbox")
        os.mkdir(sandbox)
        proc = run([juru, "--new", "packed"], cwd=sandbox)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        made = os.path.join(sandbox, "packed.jr")
        assert os.path.exists(made)
        proc = run([juru, made], cwd=sandbox)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout == (
            "hello, friend!\n"
            "level 3, progress 7.5\n"
            "step 1\nstep 2\nstep 3\n"
            "you carry 4 items\n[shield, potion]\n"
        ), proc.stdout

        # 6) the installed REPL answers
        proc = run([juru, "repl"], input="say(40 + 2)\nexit\n")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "jruru> 42" in proc.stdout, proc.stdout
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ------------------------------------------------------------------ VS Code extension
def _load_json(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return json.load(f)


def t_vscode_files_are_valid_json():
    pkg = _load_json("vscode", "juru-vscode", "package.json")
    assert pkg["name"] == "juru-vscode"
    languages = pkg["contributes"]["languages"]
    assert languages[0]["id"] == "juru"
    assert languages[0]["extensions"] == [".jr"]
    assert pkg["contributes"]["grammars"][0]["scopeName"] == "source.juru"
    assert pkg["contributes"]["snippets"][0]["language"] == "juru"
    grammar = _load_json("vscode", "juru-vscode", "syntaxes", "juru.tmLanguage.json")
    assert grammar["name"] == "JuRu" and grammar["scopeName"] == "source.juru"
    _load_json("vscode", "juru-vscode", "language-configuration.json")
    snippets = _load_json("vscode", "juru-vscode", "snippets", "juru.json")
    assert len(snippets) >= 6, "snippets must cover the main constructs"
    for prefix, snip in snippets.items():
        assert snip.get("body"), "empty snippet body: " + prefix


def t_grammar_keywords_match_the_language():
    """The editor colors exactly the keywords the language has — no drift."""
    grammar = _load_json("vscode", "juru-vscode", "syntaxes", "juru.tmLanguage.json")
    kw_pattern = grammar["repository"]["keywords"]["match"]
    head, tail = "\\b(", ")\\b"
    assert kw_pattern.startswith(head) and kw_pattern.endswith(tail), kw_pattern
    colored = set(kw_pattern[len(head):-len(tail)].split("|"))
    assert colored == set(KEYWORDS), (
        "grammar colors {} but the language has {}".format(
            sorted(colored), sorted(KEYWORDS)))


def t_vscode_docs_exist():
    with open(os.path.join(HERE, "docs", "vscode.md"), encoding="utf-8") as f:
        text = f.read()
    assert "Load from VSIX" in text or "load" in text.lower()
    with open(os.path.join(HERE, "vscode", "juru-vscode", "README.md"),
              encoding="utf-8") as f:
        assert "JuRu" in f.read()


ALL = [
    ("pyproject.toml is sound", t_pyproject_is_sound),
    ("the version has one source of truth", t_pyproject_version_is_the_only_truth),
    ("the package imports cleanly on its own", t_package_imports_cleanly),
    ("root launchers still work", t_root_launchers_work),
    ("CLI: juru.py repl subcommand", t_cli_repl_subcommand),
    ("real wheel: build → install → run → REPL", t_wheel_builds_installs_and_runs),
    ("VS Code: extension files are valid", t_vscode_files_are_valid_json),
    ("VS Code: grammar keywords == KEYWORDS", t_grammar_keywords_match_the_language),
    ("VS Code: how-to docs exist", t_vscode_docs_exist),
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
