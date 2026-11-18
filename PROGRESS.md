# JuRu — Progress Log

> Maintained alongside `ROADMAP.md`. Updated after EVERY completed
> step so progress survives context resets. The plan lives in
> ROADMAP.md; this file records what is actually done, with proof
> (test counts, commits, releases).

---

## Current state (updated 2026-11-18)

- **Version:** 1.10 — latest release **v1.10** (not draft), commit `48f2f61` on `main`.
- **Tests:** 22 suites, **760 green** (`test_step23` 56, `test_step22` 71, `test_ultimate` 56).
- **Keywords:** 21 (try, rescue). **Builtins:** 48 (fail; registry: `src/juru/stdlib.py`). **Templates:** 5.
- **CI:** both workflows (`tests`, `release`) green on the v1.10 push; release
  assets verified by download + actually running the shipped Linux binary
  (caught value/rescue/fail smoke, `2 4 6` loop, `help()` overview line
  "21 keywords + 48 builtins", 3-deep `called from` stack display, `JuRu 1.10`
  banner) and inspecting the vsix (1.10.0; grammar has try/rescue + fail,
  10th snippet present).
- **Status:** Step 2 (try / rescue — errors you can catch) shipped as v1.10;
  **awaiting "START STEP 3"** (text & formatting).

## Completed before the roadmap (batches 1–8 — do not rebuild)

| Batch | Release | What shipped (summary) | Proof |
|-------|---------|------------------------|-------|
| 1–4 | v1.2–v1.4 | language core: 19 keywords, 30 builtins, modules, checker, did-you-mean errors, caret rendering, REPL + helpdb, templates (`--new`), wheel packaging | suites lexer→step12 |
| 5 | v1.5 | VS Code extension (syntax/snippets/run button/REPL), frozen PyInstaller binaries in release zips, pipe-closed exit fix | test_step15/16/17 + release assets |
| 6 | v1.6 | Python-grade setup: REPL banner/prompt parity (`juru>`), terminal-wish nudges, `juru_icon.ico` inside juru.exe (6/6 payloads), extension icon, one-step `setup.bat`/`install.sh`, zero-config interpreter discovery (`auto`), Ctrl+Alt+J + file-tree run, real version in release notes | test_ultimate 45→50, probe 124/124 |
| 7 | v1.7 | `.jr` file icon in VS Code's Explorer via language-default icon (32×32 bold-braces variant), repo-tidy enforcement test (exact top-level file set), docs synced | test_ultimate 52, probe 138/138 |
| 8 | v1.8 | `examples/guide/` — 14 lessons covering ALL 19 keywords + `00_start_here` ramp + `tools.jr`; demos moved to `examples/test/`; `examples/README.md` walkthrough with exact outputs; main README fully linked; every reference (docs, helpdb, 6+ suites) followed the move | test_ultimate 56 (batch-8 tests: folder complete / every keyword genuinely used / every lesson runs / doc links), probe 162/162 |

## Roadmap execution log

| Step | Theme | Status | Version | Commit | Tests after | Notes |
|------|-------|--------|---------|--------|-------------|-------|
| — | Audit + roadmap | ✅ DONE (2026-11-16) | 1.8 | (this commit) | 633/20 | ROADMAP.md + PROGRESS.md created; repo-tidy test updated for the two new files; NO language changes |
| 1 | Collections & ergonomics wave 1 | ✅ DONE (2026-11-16) — v1.9 | 1.9 | `6b83535` | 704/21 | Aug-assign (`+= -= *= /= %=` on names, list items, dict values; old value read before RHS, RHS once), negative indexing (reads/writes/remove_at; legal range in the error), slice steps (Python rule; zero step refused), **17 new builtins** (insert, remove_at, clear, extend, unique, delete, items, merge, index_of, starts_with, ends_with, ord, chr, set_of, union, intersect, difference), sets (list-backed, first-seen order, ONE equality rule; `{}` stays a dict), min/max variadic, `\uXXXX` escapes, `src/juru/stdlib.py` = the one registry (mirror rule now structural). New suite `test_step22` (71). **Deliberate break, documented in CHANGELOG:** `items` is now reserved (starter renames its var to `bag`; printed text unchanged). **Preserved quirk:** `xs[0:1] = [9]` still means `xs[0] = [9]` (v1.8 behavior, test-pinned). Limitation: Windows/macOS validation is CI-only (no local pip/PyInstaller); shipped Linux binary + vsix verified by hand. |
| 2 | try / rescue | ✅ DONE (2026-11-18) — v1.10 | 1.10 | `48f2f61` | 760/22 | **Exactly 2 new keywords** (19 → 21): `try { ... } rescue as e { ... }` and `rescue { ... }` (binding optional; rescue may sit on its own line). The caught error is a value with `e.message` (exact original friendly text), `e.line`, `e.col`, `e.kind` — kind is one of **11 fixed, documented kinds** (name, type, value, arity, math, index, key, loop, input, file, fail) via `lexer.kind_for` (ordered fragment rules, default `"type"`; an explicit kind always wins, so `fail("index 9 is out of range …")` stays kind `fail`). **New builtin `fail(message)`** (48 builtins): arity `(1,1)` + non-text guard, checker and runtime print the same friendly messages, registered in helpdb (cards, `errors` group, aliases raise/throw→fail, catch/except→rescue). Semantics: only `JuRuGalti` crosses a try boundary (host bugs + `break`/`continue`/`return` signals pass through, test-pinned); the try body runs in the SAME env (clean assignments survive) while the rescue gets its own child env (`e` and rescue locals never leak; checker conservative, flow-insensitive); nested trys pick the nearest rescue (errors raised inside an inner rescue reach the outer one); func errors reach the rescue that wraps the call; arguments evaluate in the caller; module errors keep kind + stack + `source_file`. **Call stacks:** every runtime error records its JuRu call stack at the innermost user-func boundary — tuple is outermost-first, display adds `called from name (line n)` lines innermost-first after the caret; display-only, so `str(err)` is unchanged and uncaught top-level output stays byte-identical (test_step17 + CLI byte-pins green); builtins never get frames; recursion records outermost→deepest call sites. Parser: friendly errors (bare rescue, missing rescue points at the try's closing `}`, `rescue as` without a name), dump forms for both shapes; checker validates rescue blocks (binding usable, reserved names refused); REPL `looks_incomplete` counts try/rescue KEYWORD tokens (text like `say("try harder")` safe). Docs: syntax.md section 16 (forms + field + kind tables + rules), tutorial 13.1 (4 executable pinned blocks), guide lesson `14_try.jr` (15 lessons), README/design/CHANGELOG synced (counts corrected to 760/22), vscode grammar 21+48 + 10th snippet, version 1.10 / package.json 1.10.0. New suite `test_step23.py` (56 tests). Limitation: Windows/macOS validation is CI-only (no local pip/PyInstaller); shipped Linux binary + vsix verified by hand. |
| 3 | Text & formatting | ⬜ PENDING | | | | |
| 4 | Files & JSON | ⬜ PENDING | | | | |
| 5 | Math, time & constants | ⬜ PENDING | | | | |
| 6 | Classes & OOP | ⬜ PENDING | | | | |
| 7 | Modules 2.0 | ⬜ PENDING | | | | |
| 8 | Developer tools | ⬜ PENDING | | | | |
| 9 | Runtime performance | ⬜ PENDING | | | | |
| 10 | Concurrency | ⬜ PENDING | | | | |
| 11 | Networking | ⬜ PENDING | | | | |
| 12 | Security & crypto | ⬜ PENDING | | | | |
| 13 | JuStore (DB) | ⬜ PENDING | | | | |
| 14 | Package management | ⬜ PENDING | | | | |
| 15 | Ecosystem hardening | ⬜ PENDING | | | | |

## The batch loop (follow for every step — from batches 1–8)

1. `gh auth setup-git` (token expires every session — always first).
2. Baseline: full suite sweep green BEFORE touching anything
   (live count in "Current state" above).
3. Implement the step (scope locked to ROADMAP.md; no drive-bys).
4. New suite `test_step<NN>.py` + update every keyword-sensitive
   suite when keywords change (lexer, extension grammar, guide
   coverage, helpdb, README/design counts, `help()` overview line).
5. Version bump: `src/juru/version.py`, `test_ultimate` VERSION
   assert, `vscode/juru-vscode/package.json`, vsix names in docs,
   CHANGELOG entry, README badge/totals, design.md totals, ci.yml
   test-count step name.
6. Local tidy: `rm -rf build src/juru.egg-info`.
7. Full sweep again + recreate/extend `/tmp/opencode/brutal_probe_bN.py`
   (probe file dies with /tmp every session — always recreate).
8. Commit via heredoc (`git commit -F -`; backticks in `-m` get eaten
   by bash). Push `main`, tag `vX.Y`, push tag.
9. Watch `gh run list` for BOTH workflows; verify the release by
   downloading assets and actually running the Linux binary + inspect
   the vsix. Update `pr.txt` (never commit it) + this file.
10. Hinglish report to the user.

## Environment notes (per session)

- Repo: `/home/runner/workspace/JuRu` (git). Sandbox may reset `/tmp`
  — probes and check files live there, the repo persists.
- No local pip/PyInstaller; Python 3.14.7 without pip — Windows/macOS
  validation is CI-based only (release workflow), as always.
- `pr.txt` lives OUTSIDE the repo (`/home/runner/workspace/pr.txt`) —
  the repo-tidy test forbids it inside.
- Release loop needs a tag push; doc-only commits (like this audit)
  push main only, no tag, no release.

## Audit findings snapshot (2026-11-16 — what Step 1+ will fix)

Confirmed by reading all sources and by running probes against the
real interpreter (all errors are today's real messages):

- NO: `try/rescue`, `fail()`, error values, call stacks in errors.
- NO: `class`/OOP, no member calls on anything but dicts/modules.
- NO: file I/O, JSON, networking, DB, crypto, threads (`run_parallel`).
- NO: sets, tuples (tuples stay out by design), negative indexing,
  negative/step slices, `x += 1`, member writes on dicts (by design),
  multi-assign (by design).
- NO: string methods (`"hi".upper()` — `'.'` is dicts/modules only);
  text tools exist as free builtins only (30), missing: `index_of`,
  `starts_with`, `ends_with`, `ord`, `chr`, `format`, padding,
  `\uXXXX` escapes.
- NO: default params, named args, varargs, comprehensions, lambdas
  (funcs-as-values DO work, incl. higher-order calls — verified).
- NO: `floor/ceil/sign/log/exp/trig`, constants (`pi`/`e`), clock/
  date beyond `sleep`; `min`/`max` capped at 2 args; no `shuffle/pick/seed`.
- Lists: only push/pop (no insert/remove_at/clear/extend/unique);
  dicts: no delete/items/merge; text: no find-index (find = lists only).
- Engineering debt: builtin if-chain + duplicated arity tables across
  checker/interpreter (unify in Step 1's registry); no AST cache
  (Step 9); REPL without history/completion (Step 8).
- Strengths to preserve: 4-stage pipeline, checker-before-run policy,
  byte-stable error messages + caret, sandboxed modules, reserved
  builtins, runaway guards, helpdb truth tests, repo-tidy enforcement,
  full distribution story.
