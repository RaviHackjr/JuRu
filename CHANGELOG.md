# Changelog

All notable changes to JuRu. The language surface only ever grows in
small, deliberate waves — keywords are counted, guarded, and kept few.

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
