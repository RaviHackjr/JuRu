# JuRu — Development Roadmap

> JuRu = easy (easier than Python) + secure (safe like Rust).
> This file is the master plan for growing JuRu from a working,
> shipped language (v1.8) into a **complete, independent programming
> language** with an ecosystem comparable to Python's — in JuRu's own
> identity: plain English, fewer keywords, shorter syntax, security by
> design, and everything test-enforced.
>
> Companion file: `PROGRESS.md` (what is done, updated after every
> completed step). This file changes only when a step's scope is
> re-planned — progress never rewrites the plan.

---

## 0. Where JuRu stands today (complete — do NOT rebuild)

These exist, work, and are test-enforced. Future steps extend them,
never replace them.

| Area | Status (v1.8) |
|------|---------------|
| Pipeline | lexer → parser → checker → interpreter, all wired via `juru.py` / `juru` command |
| Keywords | **19**, counted and guarded: `say, if, else, while, for, from, to, in, break, continue, func, return, true, false, null, and, or, not, import` |
| Builtins | **30**, reserved (cannot be shadowed, not even as a module name), arity-checked before run |
| Types | int (arbitrary precision), float, text, bool, list, dict (text/int keys), null, func, module |
| Semantics | auto int/float, `text + number` auto-join, short-circuit and/or, bounds-checked indexing, clamped slices, one-comparison-per-line, block braces (no indentation) |
| Modules | `import "file.jr"` — name = file stem, sandboxed env, run once, loop detection, checked before run |
| Errors | `JuRuGalti` with line/col, did-you-mean everywhere, caret rendering (`errfmt.py`), message line is byte-stable |
| REPL | Python-parity banner/prompt (`juru>`), expression echo, multi-line blocks, `cancel`, terminal-wish nudges |
| Help | `help()` overview + truthful per-name cards (`helpdb.py`, test-enforced) |
| Templates | 5 (`starter`, `calculator`, `quiz`, `guessing_game`, `word_stats`) via `juru --new` |
| Docs | tutorial (test-verified), syntax cheat sheet, install, vscode, design, CHANGELOG |
| Examples | `examples/guide/` — 14 lessons covering all 19 keywords + ramp + module; `examples/test/` — 15 demos, all outputs verified |
| Distribution | wheel (`pip install juru`), frozen binaries (Windows/Linux/macOS zips with one-step `setup.bat`/`install.sh`), VS Code extension (syntax, snippets, run button, REPL, zero-config interpreter discovery, `.jr` file icon) |
| Security | no eval, no shell, runaway-loop guard (10M steps), sleep budget, guarded dict keys, sandboxed modules |
| Tests | 20 suites, **633 tests green**, `test_ultimate` 56 (combined torture, repo-tidy enforcement) |
| Releases | GitHub releases with assets verified by actually downloading and running them |

## 1. Design rules every future step must obey

1. **Identity first.** Plain-English words, `{ }` blocks, no indentation
   sensitivity, no semicolons, no single quotes, no chained
   comparisons, one statement per line. New syntax must be *shorter or
   clearer than Python's equivalent*, never merely different.
2. **Keywords are counted.** Every keyword addition is deliberate,
   documented, and gets: a guide lesson (the guide test enforces
   `covered == KEYWORDS`), grammar updates in the VS Code extension
   (test-enforced), helpdb cards, README/design counts, and a version
   bump. Target budget: stay under ~30 keywords forever.
3. **Prefer builtins over keywords.** Anything that can be a plain
   function (`floor`, `insert`, `read_file`) must not become a keyword.
4. **No duplicates.** A new builtin may not overlap an existing one:
   membership is `in` (so no `contains`), slicing is `[a:b]` (so no
   `substring`), conversion is `int`/`float`/`str` (so no `to_text`).
5. **Security by design.** No `eval`, no shell calls, no arbitrary
   code from strings, no unbounded I/O (size/time caps on file, net,
   and DB operations), every new capability gets guarded, friendly
   errors with line/col.
6. **Consistent errors.** Same style as today: one human sentence +
   the real data + did-you-mean when applicable; the message line
   stays byte-stable; caret context is display-only.
7. **Everything test-enforced.** No step is complete without its new
   test suite, the full 20-suite sweep green, and the docs/examples
   updated in the same commit.
8. **The batch loop** (unchanged from batches 1–8): version bump →
   changelog → docs sync → full sweep → brutal probe → commit →
   push → tag vX.Y → watch CI + release workflows → download and run
   the shipped binary → update `PROGRESS.md` + `pr.txt` → Hinglish
   report to the user.

## 2. Roadmap overview

| # | Step | Theme | New keywords | Depends on | Risk |
|---|------|-------|--------------|------------|------|
| 1 | Collections & ergonomics wave 1 | augmented assign, negative indexing, slice steps, list/dict/text/set power, builtin registry refactor | 0 | — | low |
| 2 | Error handling | `try` / `rescue`, error values, `fail()`, call stacks in errors | +2 (`try`, `rescue`) | 1 | medium |
| 3 | Text & formatting wave | `format()`, padding, line tools, more text builtins | 0 | 1 | low |
| 4 | Files & JSON | read/write text + lines, `to_json`/`from_json`, dir tools | 0 | 2 | medium |
| 5 | Math, time & constants | floor/ceil/log/trig, `pi`/`e` constants, clock/date, random extras | 0 (constants reserved names) | 1 | low |
| 6 | Classes & OOP | `class` (fields, methods without `self`, inheritance via `from`) | +1 (`class`) | 1, 2 | high |
| 7 | Modules 2.0 | module search path, folder packages, stdlib-style built-in modules | 0 | 1, 2 | medium |
| 8 | Developer tools | `juru --check/--doc/--tokens/--ast`, deterministic formatter, REPL 2.0 (completion, history, `:load`) | 0 | 1–5 | medium |
| 9 | Runtime performance | AST/bytecode cache (`.jrc`), dispatch optimization, benchmarks | 0 | 1 | medium |
| 10 | Concurrency | `run_parallel(funcs)` worker threads, no shared mutation | 0 | 2, 4 | high |
| 11 | Networking | `http_get`/`http_post` with guards | 0 | 2, 4 | medium |
| 12 | Security & crypto | `sha256`, `base64_encode/decode`, `random_secret` | 0 | 1, 2 | low |
| 13 | Data storage | JuStore — JSON-lines document DB (`db_open/put/get/delete/keys/close`) | 0 | 4 | medium |
| 14 | Package management | `juru --install owner/repo`, `juru --libs`, user lib dir | 0 | 7, 12 | medium |
| 15 | Ecosystem hardening | docs website, Marketplace publish, compatibility sweep, 1.0 review | 0 | 1–14 | low |

Dependency chain: 1 → {2,3,5} → {4,6,7,8,9} → {10,11,12,13} → 14 → 15.
Steps 3, 5 are independent of each other and can follow Step 2 in any
order; the numbering above is the recommended execution order.

---

## 3. The steps in detail

### Step 1 — Collections & ergonomics wave 1 (zero new keywords)

**Goal.** Remove the daily-workaround class of gaps so every later
step is built on complete data structures. Also pay down the one real
piece of internal debt: builtins live in a long `if`-chain inside the
interpreter with duplicated tables in the checker — consolidate into
one stdlib registry (single source of truth for names, arity, help
cards, and implementations) with **zero behavior change**.

**Implementation details.**

1. *Augmented assignment* — lexer gains `+=  -=  *=  /=  %=` (two-char
   ops); parser desugars `x += e` → `x = x + e` and `list[i] += e` →
   setindex. REPL continuation list gains the five tokens. Checker:
   reserved-name rules unchanged.
   ```
   x = 5
   x += 2        # 7
   xs[0] += 10   # item update, bounds-checked as today
   ```
2. *Negative indexing* — `xs[-1]` = last item (bounds-checked:
   `-len .. len-1`); error message updated in the same house style.
   Previously this was a friendly error; it becomes a feature. Old
   positive behavior untouched.
3. *Slices with negatives and a step* — `xs[-3:]`, `xs[:-1]`,
   `xs[1:7:2]`, `xs[::-1]` (lists and text). Clamping stays; negative
   bounds resolve Python-style; step must be a non-zero int.
4. *List power* (all new reserved builtins with arity + helpdb cards):
   `insert(list, i, item)`, `remove_at(list, i)` (returns the removed
   item, in place), `clear(list)`, `extend(list, more)`, `unique(list)`
   (new list, first occurrence kept).
5. *Dict power*: `delete(dict, key)` (in place; missing key = friendly
   error with the key list), `items(dict)` (list of `[k, v]` lists),
   `merge(a, b)` (NEW dict, later keys win). Membership stays `in` —
   no `has()`.
6. *min/max variadic*: `min(2, 5, 1)`, `max(xs)` — one or more args;
   a single list arg is scanned, plain numbers compared directly.
   2-arg behavior unchanged (old programs keep working).
7. *Text additions*: `index_of(text, piece)` (first index or -1 —
   mirrors `find` on lists), `starts_with(text, prefix)`,
   `ends_with(text, suffix)`, `ord(text)` (one-character text → code),
   `chr(code)` (code → text), `\uXXXX` escape in the lexer.
   Contains stays `in`.
8. *Sets* — a new value type `set`: `set_of(list)` builds it (dedup),
   `union(a, b)`, `intersect(a, b)`, `difference(a, b)` (all return
   NEW sets), `in` / `len` / `for x in` / `sorted(list_of_set?)` work,
   `display` prints `{a, b, c}` (an empty set prints `set()` — `{}` is
   a dict, forever). No set literal syntax (identity: no new delimiters).
9. *Registry refactor* — `src/juru/stdlib.py`: one table per builtin
   `(name, arity, hint, help-group, handler)`; checker and interpreter
   read from it. The BUILTINS tuple stays exported for compatibility.
   All 633 tests must stay byte-green after this refactor.

**Expected outcomes.** Builtins 30 → 45-ish (exact count locked by the
test suite); programs get markedly shorter (no manual index
arithmetic, no copy-loops for dedup/merge); the checker/interpreter
drift risk disappears.

**Testing requirements.** New suite `test_step22.py` (target ~45
tests): parser AST shapes for `+=`/slices; runtime for every new
builtin including empty/wrong-type/boundary cases (`remove_at` on
empty, `insert` past the end clamps or errors — pick and pin one),
negative-OOB messages, `ord("")` refusal, `\uXXXX` bad-hex error,
set ops with mixed types; regression sweep of all 20 suites; REPL
echo for `x += 1`; frozen-build smoke on CI; helpdb truthfulness
auto-covers the new cards.

**Docs & examples.** `docs/syntax.md` sections for each addition;
tutorial gets a "wave 5 tools" chapter mention; guide untouched
except nothing (no new keywords); design.md grammar + stdlib sections;
CHANGELOG 1.9; version → 1.9; README badge counts.

### Step 2 — Error handling: `try` / `rescue` (2 new keywords)

**Goal.** Programs that talk to files, networks and users need to
survive failure. JuRu's errors are already friendly; this step makes
them *catchable* without losing the friendliness.

**Implementation details.**

```
try {
    text = read_file("data.txt")
    n = int(text)
} rescue as e {
    say("could not load: " + e.message)
}
```

- New keywords: `try`, `rescue` (shorter than `except`, same initial
  letter as Python's flow — plain English). 19 → 21 keywords.
- A raised error becomes a VALUE inside rescue: fields `.message`,
  `.line`, `.col`, `.kind` (`"math"`, `"index"`, `"key"`, `"file"`, …).
  Kind list is fixed and documented.
- New builtin `fail(message)` — raises a JuRu error from user code
  (the keyword-free way to signal). Reserved, arity-guarded.
- `rescue` without `as e` also valid. Optional `try`/`rescue` +
  `always`-style cleanup is NOT in this step (no new keyword for it;
  reconsider only if real use asks).
- Interpreter: catch `JuRuGalti` at the try boundary; every raise
  gains a recorded call-stack (display-only, like errfmt's caret) so
  runtime errors show "called from …" lines. Message line stays
  byte-stable for top-level errors.
- Checker: `try` blocks are new scopes; `e` in `rescue as e` is
  assigned; validate calls inside normally.

**Expected outcomes.** Real programs can recover; error kinds make
rescues precise; the call stack makes debugging deep calls possible.

**Testing requirements.** `test_step23.py` (~35): rescue catches each
error kind; `e.message` exact text; nested try; fail() raises and is
rescued; unrescued errors still print exactly as today (regression!);
REPL: a failed try does not kill the session; checker rejections;
guide lesson for `try`/`rescue` (guide test enforces coverage of the
new keywords); grammar/snippets/helpdb/README counts updated.

### Step 3 — Text & formatting wave (zero new keywords)

**Goal.** Bring text output and manipulation to daily-use level.

**Implementation details.** `format(text, values...)` — `{}` slots
filled left to right, `{0}` explicit, `{{`/`}}` literals (NO
expression embedding — that is eval's little brother; JuRu formats
values, not code): `format("x={0} y={1}", x, y)`. `pad_left(text, n)`,
`pad_right(text, n)`, `center(text, n)`, `split_lines(text)`,
`join_lines(list)`, `repeat(text, n)`? NO — `"ab" * 3` already exists
(avoid duplicates). `to_title(text)`? Only if a real use; keep the
wave tight: format + pad×2 + center + split_lines + join_lines.

**Expected outcomes.** Tables, reports and CLI-style output without
manual space arithmetic.

**Testing requirements.** `test_step24.py` (~20): slot order, mixed
`{}`/`{0}` (decide: error — pin it), overflow slots, pad with wide
characters, empty lists; regression sweep; syntax.md + tutorial
blocks; helpdb cards.

### Step 4 — Files & JSON (zero new keywords)

**Goal.** Real programs read and write data. JuRu does it with caps
and clean errors, no shell, no globs.

**Implementation details.**

- `read_file(path)` → text (UTF-8; cap 10 MB, friendly error above),
  `write_file(path, text)` (overwrite), `append_file(path, text)`,
  `read_lines(path)` → list (no trailing `\n`s), `write_lines(path, list)`,
  `file_exists(path)`, `file_size(path)`, `delete_file(path)`
  (refuses directories), `list_dir(path)` → sorted names,
  `make_dir(path)` (single level; parents via `make_dirs`? — no:
  `make_dir` creates parents, one function), `delete_dir(path)`
  (empty dirs only — no recursive rm, ever).
- Paths: relative paths resolve against the program's directory
  (same rule imports use). No `~` expansion, no `..` refusal (honest
  tool, guarded sizes), no glob patterns.
- `to_json(value)` → text (dict/list/num/text/bool/null only; func/
  module = friendly error), `from_json(text)` → value (dicts get
  text keys — JSON has no int keys; nested depth cap 64; size cap).
- All file functions accept an optional `try`-rescuable `kind:
  "file"` error family (Step 2 dependency).

**Expected outcomes.** Configuration, data files, and JSON APIs
usable from JuRu on day one — inside the official distribution, zero
install (the mandate: stdlib ships with the interpreter).

**Testing requirements.** `test_step25.py` (~40): round-trips
(write→read→equal), append, lines with unicode, size-cap refusals,
delete-missing, list_dir sorting, JSON edge cases (unicode escapes,
nested, big depth, bad text, float formatting — pin Python-JSON
float display), from_json key collision, permissions errors surfaced
friendly. Docs: syntax.md chapters, tutorial "files" chapter,
`help()` groups.

### Step 5 — Math, time & constants (zero new keywords)

**Goal.** Complete the numeric toolbox; give programs a clock.

**Implementation details.** Reserved CONSTANTS (like `true`/`null`,
cannot be assigned): `pi`, `e`. Builtins: `floor(x)`, `ceil(x)`,
`sign(x)`, `log(x)` (natural), `log10(x)`, `exp(x)`, `sin/cos/tan(x)`
(radians), `degrees(x)`, `radians(x)`. Time: `clock()` (seconds,
float — for timing), `now()` (unix seconds float), `date_text(now())`
→ `"2026-11-16 14:03:00"` (local time, one format, no locale zoo),
`date_parts(now())` → dict `{"year", "month", "day", "hour", "minute", "second"}`.
Random extras: `pick(list)` (one item), `shuffle(list)` (NEW shuffled
list), `seed_random(n)`. `mean(list)`, `round_to(x, digits)`
(round(x) stays as-is — no duplicate).

**Testing requirements.** `test_step26.py` (~30): value checks with
tolerance for trig, constants' exactness vs Python, date formatting
pinned, shuffle/pick with seeded determinism, empty-list refusals
friendly. Docs + helpdb cards.

### Step 6 — Classes & OOP: `class` (1 new keyword)

**Goal.** Objects for bigger programs — JuRu style: shorter than
Python, no ceremony.

**Implementation details.**

```
class Dog {
    func new(name) {          # constructor: func new(...)
        this.name = name      # 'this' — the one new reserved NAME (not a keyword)
    }
    func bark(d, times) {     # first param IS the instance; no 'self' ceremony
        return d.name + " barks " + str(times) + " times"
    }
}
class Puppy from Dog {        # inheritance — reuses the existing 'from' keyword
    func bark(d, times) {     # override
        return "yip! " + Dog.bark(d, times)
    }
}

d = Dog("Rex")                # calling the class constructs
say(d.bark(2))                # method call: d.bark(2) → bark(d, 2)
say(d.name)                   # field read via member (d["name"] sugar already exists)
d.age = 1                     # field write via member (new: member assignment allowed on instances)
```

- New keyword `class`; new reserved word `this` (a NAME, not a
  keyword — usable as a normal name? No: reserved inside classes,
  friendly error outside). 21 → 22 keywords.
- Methods are plain funcs stored on the class; `obj.method(args)`
  desugars to `method(obj, args...)` — so the guide's funcs knowledge
  transfers 1:1. Explicit call `Dog.bark(d, 2)` also works.
- Fields live in the instance's env (a dict internally); member read
  `d.x` = field; member WRITE `d.x = v` becomes legal for instances
  (still illegal for dicts — that rule stays, message unchanged).
- Instances are a new type name `"object"` from `type()`; `display`
  prints `<Dog name=Rex>`-style (pinned format).
- No multiple inheritance, no metaclasses, no operator overloading,
  no properties — JuRu stays JuRu. Duck typing via `type()`/`type(x) == "object"`.
- Checker: field names cannot be checked statically (conservative —
  same policy as module members); constructor arity IS checked when
  unambiguous.

**Testing requirements.** `test_step27.py` (~50): construct/field/
method/override/super-call (`Dog.bark(d, …)`), `this` rules, member
write, inheritance chains (2 levels), constructors with wrong arity,
instances in lists/dicts, display format, type() name, interaction
with try/rescue, REPL flow. Guide lesson for `class` (coverage test
forces it). Grammar, snippets, README keyword count 22, design.md.

### Step 7 — Modules 2.0: search path & packages (zero new keywords)

**Goal.** Bigger projects and reusable libraries without changing the
language.

**Implementation details.**

- Resolution order for `import "x.jr"`: (1) next to the importing
  file (today's rule, unchanged), (2) the program's `lib/` folder,
  (3) the user library dir (`~/.juru/libs`), (4) built-in library
  modules shipped inside the interpreter (see below). First hit wins;
  the error lists everywhere it looked (today's style).
- Folder packages: `import "utils/list.jr"` — module name is the
  full stem with `/` → `_` (`utils_list`) … OR nested module access
  `utils.list.push(...)`? Pin ONE: sub-path import gives module
  `utils_list` (simple, no new syntax). Decision point at
  implementation; default = flat stem name.
- Built-in modules: the standard library ALSO ships as importable
  modules (`import "math.jr"` → the Step-5 math builtins namespaced;
  `import "file.jr"`, `"json.jr"`, `"time.jr"`) for people who prefer
  namespaces — while the flat builtins remain (both work; no
  duplication of logic, modules are thin views over the registry).
- `juru --path` prints the search path (debugging aid).

**Testing requirements.** `test_step28.py` (~30): resolution order
with shadowing, lib folder, user dir (temp HOME), built-in module
import, run-once across paths, error messages listing searched
locations. Docs: tutorial modules chapter rewrite, syntax.md.

### Step 8 — Developer tools (zero new keywords)

**Goal.** The tooling Python users expect, JuRu-shaped.

**Implementation details.**

- `juru --check file.jr` — checker only, exit 0/1 (CI-friendly).
- `juru --tokens file.jr` / `juru --ast file.jr` — the existing
  lexer/parser CLIs surfaced on the main command (also enter the
  frozen binary).
- `juru --doc name` — helpdb cards from the terminal.
- `juru --fmt file.jr [--write]` — deterministic formatter: one
  statement per line, 4-space indents inside `{}`, spaces around
  operators, aligned comments OFF (never reflows comments). Round-trip
  guarantee: fmt(fmt(x)) == fmt(x), and fmt never changes semantics
  (checked by running before/after in tests).
- REPL 2.0: readline-backed history file (`~/.juru/history`),
  tab completion of names/builtins/keywords, `:load file.jr` runs a
  file into the session, `:doc name`, `:env` lists names. Everything
  degrades gracefully when readline is missing (Windows).

**Testing requirements.** `test_step29.py` (~35): check exit codes,
tokens/ast output stability, fmt idempotence + semantics-preservation
across all examples/guide files, REPL completion/hist with a stubbed
input. Docs: new `docs/tools.md`.

### Step 9 — Runtime performance (zero new keywords)

**Goal.** Same language, faster runs — honestly measured.

**Implementation details.**

1. Dispatch: interpreter statement/eval dispatch via dict-of-handler
   (done partly in Step 1's registry refactor; complete here).
2. AST cache: after a successful parse+check, serialize the checked
   tree to `<file>.jrc` (versioned magic + source mtime/hash);
   subsequent runs load it directly. Cache is opt-out via
   `--no-cache`; corrupted/foreign caches are ignored, never fatal.
3. Constant folding for literal arithmetic at parse; env-chain
   fast path for globals (top-level programs are one frame).
4. Benchmarks committed as an example (`examples/test/bench.jr`)
   with a runner test asserting *no regression* beyond a threshold
   (loose enough for CI noise; strict locally).

**Expected outcomes.** ≥2× on loop-heavy programs from cache hits;
cold start comparable (cache write is one-time).

**Testing requirements.** `test_step30.py` (~20): cache create/reuse/
invalidate-on-edit/ignore-on-corrupt, `--no-cache`, folding
correctness (`0.1 + 0.2` still honest float), bench smoke. Full
regression sweep is critical here (interpreter internals touched).

### Step 10 — Concurrency (zero new keywords)

**Goal.** Do several waiting-things at once, safely.

**Implementation details.**

- `run_parallel(list_of_funcs)` → list of results in the same order
  (worker threads; results collected via a queue; exceptions inside
  a worker become error values — Step 2's error values — in that
  slot, so one failure never poisons the batch).
- Rules that keep it JuRu-safe: funcs receive no shared mutable
  state by design — args are deep-copied into the worker (copy-in,
  results copy-out); no locks, no atomics, no `thread` keyword.
  `sleep`, `http_*`, `read_file` are the real wins (I/O-bound);
  CPU-bound speedups are NOT promised (honest docs).
- Cap: 32 workers max; zero funcs → empty list.

**Testing requirements.** `test_step31.py` (~25): ordering, arg
copying (mutation inside worker invisible outside), exception slots,
worker cap, nested parallel refusal (friendly error), integration
with `run_parallel([sleep])` timing sanity (loose).

### Step 11 — Networking: HTTP client (zero new keywords)

**Goal.** Talk to the web inside the security rules.

**Implementation details.**

- `http_get(url)` → dict `{"status": 200, "body": "…", "headers": {…}}`.
- `http_post(url, body, content_type)` → same shape.
- Guards: only `http://`/`https://`; timeouts (connect 10 s, total
  30 s); response cap 2 MB (friendly error above); max 5 redirects;
  header dict keys lowercased; no cookies, no proxies, no raw
  sockets in this step.
- Errors are rescuable file/net-kind values (Step 2).

**Testing requirements.** `test_step32.py` (~25) against a local
threaded test server spun up inside the suite (no internet in CI):
status/body/headers, timeout, oversize refusal, scheme refusals,
post content-type. Docs: syntax.md "network" chapter.

### Step 12 — Security & crypto (zero new keywords)

**Implementation details.** `sha256(text)` → hex, `sha256_file(path)`,
`base64_encode(text)`, `base64_decode(text)` (strict — bad input =
friendly error), `random_secret(n)` (n bytes, 1–256, from the OS
secure pool). All stdlib-backed, size-capped, helpdb-carded.

**Testing requirements.** `test_step33.py` (~20): known-answer
vectors (pinned hashes), strict base64 refusals, secret length/uniqueness.
Docs: "secrets" section.

### Step 13 — Data storage: JuStore (zero new keywords)

**Goal.** Persistence between runs without SQL or servers.

**Implementation details.**

- JSON-lines append-only store: `db_open(path)` → handle (creates or
  opens; compacts on open if >4× garbage), `db_put(db, key, dict)`,
  `db_get(db, key)` (missing → null — call sites check, or rescue),
  `db_delete(db, key)`, `db_keys(db)` (sorted), `db_count(db)`,
  `db_close(db)` (flush; open handles auto-close at program end —
  interpreter shutdown hook).
- Keys: text only. Values: any JSON-able JuRu value (Step 4 rules).
- One writer at a time per path (second `db_open` on the same file =
  friendly "already open" error). All I/O capped.

**Testing requirements.** `test_step34.py` (~30): put/get/delete/
reopen-persistence, compaction, key rules, value rules (func refuses),
double-open refusal, crash-safety (kill mid-write simulation →
open recovers last complete line). Docs: "store" chapter.

### Step 14 — Package management (zero new keywords)

**Goal.** `git clone`-free library sharing, Python-pip-shaped but tiny.

**Implementation details.**

- Convention: a library repo contains `lib.jr` (entry) + optional
  files; a pinned release is a GitHub tag.
- `juru --install owner/repo` (optional `@tag`): downloads the
  GitHub zip, verifies it contains `lib.jr`, installs into
  `~/.juru/libs/<repo>`, refuses overwrites without `--upgrade`.
- `juru --libs` lists name + version (from a tiny `meta` dict the
  library may expose via `lib.meta`), `juru --uninstall name`.
- Usage stays plain `import "repo/lib.jr"` (Step 7's search path).
- No dependency resolution graph in v1 (one-level installs, honest
  docs); no arbitrary code runs at install time (only file moves).

**Testing requirements.** `test_step35.py` (~25) against a fixture
local zip path + a stubbed downloader: install/upgrade/refuse,
corrupt zip refusal, no-`lib.jr` refusal, uninstall, search-path
integration. Docs: `docs/packages.md`.

### Step 15 — Ecosystem hardening & 1.0 review

- Docs website (static, generated from the existing docs).
- VS Code Marketplace publish (needs publisher account).
- Full compatibility sweep: every released example/guide/template
  re-verified on the final build; semver review of everything added
  since 1.8; deprecation pass (nothing planned).
- The 1.0 release: language + stdlib + tools declared stable, with
  the compatibility promise written into design.md.

---

## 4. Testing & verification strategy (every step, no exceptions)

1. **Full sweep first** — all 20 existing suites green before any new
   work starts (known-good baseline).
2. **New suite per step** — `test_step<NN>.py`, named for the design
   roadmap step (22, 23, …), covering: happy paths, edge cases
   (empty, zero, huge, unicode), invalid inputs (every wrong type),
   runtime errors (exact friendly messages, pinned), REPL behavior,
   checker rejections, frozen-binary smoke on CI.
3. **Regression testing** — after implementation, the full 20+ suites
   again, byte-identical old outputs (any intentional message change
   is listed in the step, updated in one place, and covered by tests
   on BOTH sides).
4. **Keyword-sensitive suites** — lexer KEYWORDS, extension grammar
   (test-enforced), guide coverage (`covered == KEYWORDS`), helpdb
   truthfulness, README/design counts, `help()` overview line.
5. **Brutal probe** — a fresh `/tmp/opencode/brutal_probe_bN.py`
   (150+ checks: new surfaces + all previous batches' surfaces).
6. **Release verification** — download the shipped Linux binary and
   actually run programs on it; unzip the vsix and inspect; verify
   release notes + assets; only then report success.
7. **Never hide a red test.** Failures are fixed or the step is not
   complete; the user always gets the true final count.

## 5. Explicitly out of scope (identity guard)

- No `eval`, no shell/process execution, no arbitrary code from
  strings, no raw sockets.
- No indentation-based blocks, no colons-after-blocks, no semicolons,
  no single-quoted strings, no chained comparisons.
- No f-strings with embedded expressions (Step 3's `format()` covers
  the need safely).
- No operator overloading, no metaclasses, no properties, no
  decorators, no generators/`yield` (revisit only if a real use
  demands; async is not planned — threads via Step 10 cover the need).
- No type annotations (JuRu stays dynamically typed with `type()`).
- No silent behavior changes: any message or rule change is listed
  in the step, in CHANGELOG, and double-tested.

---
*Roadmap created 2026-11-16 after the full v1.8 audit (batch 8,
commit `dc2a49d`). Next action: user says "START STEP 1".*
