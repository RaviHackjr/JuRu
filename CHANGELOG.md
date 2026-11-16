# Changelog

All notable changes to JuRu. The language surface only ever grows in
small, deliberate waves — keywords are counted, guarded, and kept few.

## 1.7 — 2026-11-16

### Added
- `.jr` files now carry the JuRu ruby in **VS Code's file tree** — the
  same way Python files show theirs. The language icon
  (`images/juru-file-icon.png`, a small-size variant of the logo with
  bolder braces) works with any icon theme — Seti, Material, anything —
  with no settings and no clicks.
- The repository itself is kept deliberately clean: the test suite now
  enforces the exact top-level file set (no stray files, no build
  junk, `pr.txt` never in the repo).

### Details
- 30 builtins, still 19 keywords.
- 20 test suites, 629 tests.

## 1.6 — 2026-11-16

### Changed
- The REPL greets you the way Python's does:
  `JuRu 1.6 (easy like Python, secure like Rust) on win32` plus a
  `Type "help", "exit" or "cancel" for more information.` line. The
  prompt is `juru>` — the same name as the command, so the old
  `jruru>` confusion is gone for good.
- A terminal command pasted into the REPL (`juru --version`, `pip`,
  `--version`, `dir`, ...) now answers with one friendly line — this is
  the REPL, exit first, then run it in your terminal (and for `pip`:
  JuRu needs no pip, everything is built in) — instead of a
  "'juru' was not found" error. Real JuRu code that uses those names
  (`juru = 5`, `juru + 3`) still runs exactly as code.

### Added
- One-step setup, like a real installer: the Windows zip carries
  `setup.bat`, which installs the interpreter to
  `%LOCALAPPDATA%\Programs\JuRu` (Python's per-user spot), adds it to
  your PATH, and gives `.jr` files the JuRu icon in Explorer with
  double-click run. The macOS/Linux zips carry `install.sh`.
- Real icons: `juru.exe` carries the JuRu ruby (Explorer, taskbar, the
  `.jr` file icon), and the VS Code extension has its official icon
  (`images/juru.png`).
- The extension finds the interpreter by itself — PATH, then the
  one-step-setup location (`%LOCALAPPDATA%\Programs\JuRu`,
  `/usr/local/bin`, `~/.local/bin`). Nothing to configure, ever. The
  run button also gained **Ctrl+Alt+J** and the file-tree right-click
  menu, and `juru.interpreterPath` defaults to `auto`.

### Details
- 30 builtins, still 19 keywords.
- 20 test suites, 627 tests.

## 1.5 — 2026-11-15

### Added
- `help()` — built-in documentation: `help()` lists the whole toolbox,
  `help("name")` prints one card with worked examples and its real guard
  messages. 48 cards (30 builtins + 19 keywords), aliases like
  `power` → `pow`, and did-you-mean for unknown names.
- `sleep(seconds)` — pause a program, with guards: numbers only, no
  negatives, at most 30 s per call, at most 120 s per run.
- The bare `juru` command now opens the REPL, exactly like bare `python`.
  The REPL banner advertises `help()`, and bare `help` (or `?`) prints
  the toolbox without parentheses.
- Errors now show the offending source line with a caret under the exact
  column, in the CLI and the REPL. Module errors point into the module's
  own file. When the source is unavailable the output falls back to the
  plain message — never a wrong line, never a traceback.
- Standalone interpreters (Windows / Linux / macOS) are built on release
  and attached to the GitHub release as zips; the VS Code extension
  gained a run button (`JuRu: Run File`) and `JuRu: Open REPL`.

### Details
- 30 builtins (`+help`, `+sleep`), still 19 keywords, 48 help cards.
- 20 test suites, 619 tests.

## 1.4 — 2026-11-14

### Added
- Stdlib wave 3: `float`, `pow`, `pop`, `type` (still zero new keywords —
  28 builtins at this point).
- pip packaging: `pip install juru`, the `juru` command, templates inside
  the wheel; a test installs the real wheel into a fresh venv.
- Official VS Code extension, prepare-only: TextMate grammar, snippets,
  language configuration.

## 1.3 — 2026-11-13

### Added
- Templates: five starter programs (`starter`, `calculator`, `quiz`,
  `guessing_game`, `word_stats`) and the `--new` / `--templates` CLI.
- `docs/tutorial.md` — the whole language in one sitting, executable and
  enforced by tests so it cannot drift from the truth.

## 1.2 — 2026-11-13

### Added
- Stdlib wave 2: `sorted`, `reverse`, `find`, `keys`, `values`, `count`.
- Everything from batch 1: lexer, parser, checker, interpreter, the
  REPL, dicts, `for x in`, membership, slices, modules with run-once
  caching and import-loop detection, did-you-mean typos, the multi-line
  REPL with `cancel`, and runaway-loop protection.
