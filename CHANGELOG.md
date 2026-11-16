# Changelog

All notable changes to JuRu. The language surface only ever grows in
small, deliberate waves — keywords are counted, guarded, and kept few.

## 1.9 — 2026-11-16

Step 22 — **collections & ergonomics wave 1**. Lists, dicts, text and
sets get their power tools; the language stays 19 keywords big and every
old message stays byte-identical except the ones listed under *Changed*.

### Added
- **Augmented assignment**: `x += 1` (also `-=`, `*=`, `/=`, `%=`) on
  plain variables, list items and dict values — `nums[0] += 1`,
  `d["score"] += 10`, perfect for loop counters. The old value is read
  before the right side is evaluated, and the right side runs exactly once.
- **Negative indexing**: `nums[-1]` is the last item, `text[-2]` the
  second-to-last — in reads, writes and `remove_at`. Past the start is
  still a friendly error that shows the legal range:
  `index -4 is out of range — this list has 3 items (-3 to 2)`.
- **Slice steps**: `[::-1]` reverses, `[::2]` takes every second item,
  `[1:7:2]` slices with a stride — Python's rule, exactly. Negative bounds
  count backwards now (`nums[-3:]` is the last three), clamps still hold,
  and a zero step is refused in words: `the slice step cannot be zero`.
- **17 new reserved builtins** (all guarded by the checker *and* the
  runtime, with human error messages):
  `insert(list, i, item)`, `remove_at(list, i)`, `clear(list)`,
  `extend(list, more)`, `unique(list)`, `delete(dict, key)`,
  `items(dict)`, `merge(a, b)`, `index_of(text, piece)`,
  `starts_with(text, prefix)`, `ends_with(text, suffix)`, `ord(x)`,
  `chr(x)`, `set_of(list)`, `union(a, b)`, `intersect(a, b)`,
  `difference(a, b)`.
- **Sets**: `set_of([3, 1, 3])` → `{3, 1}` — no duplicates, first-seen
  order, JuRu's own equality (`true != 1`, `1 == 1.0`, order-insensitive
  set equality). Sets work with `len`, `in`, `for x in`, `sorted`,
  truthiness (`set()` is false), and display as `{a, b}` / `set()`.
  `{ }` alone is still a dict — sets have no literal.
- **min/max variadic**: `min(3, 9, 1)`, `min([7, 2, 4])` — one or more
  numbers, or a whole list. The old two-argument form and its exact
  error messages are untouched.
- **`\uXXXX` escapes** in text: exactly 4 hex digits (`"\u0041"` → `"A"`),
  reserved surrogate codes (55296–57343) refused with a pointer to pick
  another character.
- The builtin registry moved into one table (`src/juru/stdlib.py`):
  names, arities and the exact wrong-count messages live there once; the
  checker and the interpreter both read it, so they can never drift
  apart (the mirror rule is now structural).
- VS Code grammar colors all 47 builtins and the five augmented
  operators; `help()` grew a truthful card for every new tool (66 cards
  total), a "sets" group, and the aliases `remove` → `remove_at`,
  `del` → `delete`.

### Changed (deliberate, documented)
- **`items` is now a reserved builtin** — a variable or func named
  `items` stops compiling:
  `'items' is reserved (builtin) — pick another name`. Rename it
  (the starter template now calls its inventory `bag`). This is the
  price of `items(dict)` being a real tool; every other old program
  runs unchanged.
- Two messages learned a fourth and fifth allowed type (sets):
  `'for x in ...' needs a list, text, dict, or set — got: 5` and
  `'in' needs a list, text, dict, or set on the right — got: 5`.
  Same for `len`: `'…' has no length — only text, lists, dicts and sets do`.
- The unknown-escape hint now lists `\u`:
  `only \n, \t, \", \\ and \u work`.
- Negative slice bounds are a feature now — the old refusals
  (`the slice start cannot be negative`) are gone, replaced by Python
  semantics and a zero-step guard.

### Details
- 47 builtins, still 19 keywords.
- 21 test suites, 704 tests.

## 1.8 — 2026-11-16

### Added
- A **beginner guide** under `examples/guide/`: 14 small, runnable
  lessons — one keyword per lesson — covering all **19 keywords** of
  the language, plus a ramp (`00_start_here.jr`) and the `tools.jr`
  module the import lesson uses. Deterministic by design: no
  randomness, no questions, same output every run.
- `examples/README.md` — the guide itself: how to run a lesson, a
  teaching walkthrough with the exact output of every lesson, and
  links to everything.
- The main README links every lesson and every demo directly.

### Changed
- The 15 demo programs moved from `examples/` to `examples/test/` —
  the guide lives beside them in `examples/guide/`. Every reference
  (docs, tests, help cards) follows the move.

### Details
- 30 builtins, still 19 keywords.
- 20 test suites, 633 tests.

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
