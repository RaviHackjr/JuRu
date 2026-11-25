# JuRu — Design Document

> **JuRu** = easy (easier than Python) + secure (safe like Rust).
> **File extension: `.jr`** — runner: `python3 juru.py program.jr`

## Goal

1. **Easy** — few keywords, human error messages, runs with zero setup.
2. **Conversation feel** — plain English keywords; reading code feels like
   talking: `say(...)`, `if ... else`, `for i from 1 to 10`, `for x in items`.
3. **Secure by design** — no pointers, no null-bug class, no eval, garbage
   collected, everything checked.

## The icon

`logo/juru_icon.svg` — a faceted ruby: the crown glows **Jupyter orange**
(`#F3801F`), the pavilion sinks into **Ruby red** (`#B31226`), and a pair of
white `{ }` braces is carved into the gem. JuRu = **Ju**pyter + **Ru**by — the
icon tells the whole story. Pure SVG, so it scales to any size.

## Status: fully working language (end to end)

The pipeline, all connected (nothing skipped, nothing breaks):

```
.jr file → lexer.py → parser.py → checker.py → interpreter.py → output
              tokens      AST         semantic         runs your code
                                        ok?

REPL mode: python3 repl.py  (same pipeline, one line at a time,
                             one shared environment)
```
`juru.py` wires them together in one command: `python3 juru.py program.jr`

| Piece | What it does | Tests |
|-------|--------------|-------|
| `lexer.py` | source text → tokens (aug ops, `\uXXXX` escapes) | **55 pass** |
| `parser.py` | tokens → AST + parse-time safety checks | **111 pass** |
| `checker.py` | semantic checks before running (Steps 3 + 5, registry in stdlib.py) | **47 pass** |
| `interpreter.py` | runs the AST + the stdlib + modules (Steps 4–7, 12, 15–16, 22) | **93 pass** |
| `stdlib.py` | the ONE builtin registry: names, arities, hint messages | in test_step12/22 |
| `helpdb.py` | the `help()` knowledge base — 75 truthful cards (Steps 15+22+23+24) | in test_step15 |
| `errfmt.py` | error display: line + caret under the exact column (Step 17) | in test_step17 |
| `juru.py` | `.jr` runner (`python3 juru.py file.jr`); bare → REPL (Step 16) | tested via checker suite |
| `repl.py` | interactive REPL (Steps 5+8, banner + bare `help` in Step 16) | **10 pass** |
| `test_programs.py` | 3 heavy programs: primes/gcd, algorithms, game | **13 pass** |
| `test_stdlib.py` | the Step 5 builtins, both layers, mirror rule | **25 pass** |
| `test_repl.py` | REPL behaviour, end to end via subprocess | **10 pass** |
| `test_mega.py` | the combined torture test of steps 1–5 | **14 pass** |
| `test_step6.py` | dicts, for-in, in/not-in, slices, strings, math | **46 pass** |
| `test_step7.py` | modules: import, run-once, loops, isolation | **17 pass** |
| `test_step8.py` | did-you-mean + the multi-line REPL | **19 pass** |
| `test_step9.py` | sorted/reverse/find/keys/values/count | **23 pass** |
| `test_step12.py` | float/pow/pop/type + all their guards | **22 pass** |
| `test_step15.py` | help(): truthful cards, aliases, unknowns, guards | **15 pass** |
| `test_step16.py` | sleep() guards + the bare-`juru` REPL | **13 pass** |
| `test_step17.py` | line + caret error display, CLI + REPL + modules | **10 pass** |
| `test_step22.py` | collections & ergonomics wave 1, both layers | **71 pass** |
| `test_step23.py` | try/rescue: catchable errors, kinds, stacks | **56 pass** |
| `test_step24.py` | text & formatting wave: format, padding, lines | **24 pass** |
| `test_templates.py` | the 5 templates + the `--new`/`--templates` CLI | **24 pass** |
| `test_tutorial.py` | docs/tutorial.md is executable and truthful | **11 pass** |
| `test_packaging.py` | real wheel → venv install → `juru` command | **9 pass** |
| `test_ultimate.py` | steps 1–23 combined, no mercy | **56 pass** |
| `examples/` | guide: 15 lessons covering all 21 keywords · test: 15 demo `.jr` files, every output exactly verified | inside suites |
| **Total** | | **784 tests green** |

Run everything yourself:
```
python3 test_lexer.py
python3 test_parser.py
python3 test_checker.py
python3 test_interpreter.py
python3 test_programs.py
python3 test_stdlib.py
python3 test_repl.py
python3 test_mega.py
python3 test_step6.py
python3 test_step7.py
python3 test_step8.py
python3 test_step9.py
python3 test_templates.py
python3 test_tutorial.py
python3 test_ultimate.py
```

## Keywords (21 — plain English)

| JuRu | Python | JuRu | Python |
|------|--------|------|--------|
| `say` | print | `break` | break |
| `if` | if | `continue` | continue |
| `else` | else | `func` | def |
| `while` | while | `return` | return |
| `for` | for | `true` | True |
| `from` | (range start) | `false` | False |
| `to` | (range end) | `null` | None |
| `in` | in / `x in d` keys | | | 
| | | `and` | and |
| | | `or` | or |
| | | `not` | not |
| `import` | import | `try` | try |
| | | `rescue` | except (catches errors) |

`else if` is written as two words — no separate `elif` keyword needed.
Builtins (reserved names): `ask(prompt)`, `len(x)`, `int(x)`, `upper(x)`,
`lower(x)`, `str(x)`, `push(list, item)`, `sum(list)`, `min(a, b)`, `max(a, b)`,
`split(text, sep)`, `join(list, sep)`, `trim(text)`, `replace(text, old, new)`,
`abs(x)`, `round(x)`, `random(low, high)`, `sqrt(x)`,
`sorted(list)`, `reverse(list)`, `find(list, item)`, `keys(dict)`,
`values(dict)`, `count(list, item)`, `fail(message)`.

## Operators

- Math: `+ - * / %` (int/float promote automatically, `/` always true division)
- Assign/compare: `= == != < <= > >=`
- Membership: `in`, `not in` (two words, one operator — compare level)
- Slice: `[a:b]`, `[a:]`, `[:b]` (lists and text; clamps, never crashes)
- Structure: `( ) { } [ ] , : .`
- Bonus: `"text" + anything` → text, `"ab" * 3` → repeat, `[1] + [2]` → join lists

## Rules (syntax)

1. File extension = `.jr`; a statement ends with a new line (no semicolons).
2. Blocks = `{ }` — **no indentation headaches**.
3. Comment = `#` to the end of the line.
4. Text = only double quotes `"..."`, escapes: `\n \t \" \\`.
5. Numbers = int (`10`) and float (`3.14`) — they promote automatically.
6. Names = letters + digits + `_` (unicode letters work, Devanagari included).
7. Error messages = human language, with line/col.
8. `for i from 1 to 5` — the `to` value is **included**; start > end counts down.
9. `for x in items` — lists walk items, text walks characters, dicts walk keys.
10. `break`/`continue` only in loops; `return` only in funcs — caught at parse time.
11. One statement per line; a line may continue after an operator.
12. `import "file.jr"` — the module name is the file's stem; access via `module.name`.

## Language semantics (all test-verified)

- **Division**: `10 / 4` → `2.5` (always true division, float result).
- **Auto-promote**: int ⊕ float → float; no silent truncation traps.
- **Text joins anything**: `"Level " + 3` → `"Level 3"`; lists/funcs refuse.
- **Text repeat**: `"ab" * 3` → `"ababab"` (whole int ≥ 0 only; the result can
  never pass 10,000,000 characters — a friendly error instead of a freeze).
- **Equality categories**: `true != 1` (bool vs number = different worlds),
  but `1 == 1.0` (same number family). ONE rule drives everything — `==`,
  `in`, `find`, `count`, `unique` and set membership/equality (order does
  not matter inside a set).
- **Truthiness**: `null`, `0`, `""`, `[]`, `{}`, an empty `set()` are false;
  everything else true.
- **Short-circuit**: `and`/`or` never evaluate the right side unnecessarily.
- **Scoping**: assignment inside a func is local; reads walk the parent chain
  (recursion works through the global env). `import` inside a func is a local
  binding.
- **Indexing**: always bounds-checked, int only; negative indexes count
  backwards (`-1` is the last item; `-len` is the first) — past the start
  is a friendly error that shows the legal range:
  `index -4 is out of range — this list has 3 items (-3 to 2)`.
- **Dicts**: keys are text or whole ints (bool/float/null/list rejected with a
  human message); missing keys are friendly errors that list the keys that DO
  exist (≤ 6 shown, otherwise the count; empty → `this dict is empty`);
  display without quotes: `{name: Aman, age: 20}`; insertion order kept;
  dicts are references — `same = d` aliases one dict; assignment needs
  `d["key"] = value` (`d.key = value` is refused with the fix in the message).
- **for x in ...**: walks a **copy** of the list (pushing during the loop is
  safe), one char at a time for text, keys for dicts, values in order for
  sets; wrong types rejected:
  `'for x in ...' needs a list, text, dict, or set — got: 5`.
- **Slices**: `[a:b]` and `[a:b:step]` on lists/text, Python's rule exactly:
  open ends follow the step's sign, negative bounds count backwards, every
  bound **clamps** (never crashes); a zero step is refused
  (`the slice step cannot be zero`) and non-int bounds stay friendly errors;
  `say([1:2])` parses as the dict `{1: 2}` (and then fails the dict-key
  check — consistent with the grammar).
- **Augmented assignment**: `x += e` (also `-=`, `*=`, `/=`, `%=`) on names,
  list items and dict values — the old value is read BEFORE the right side
  is evaluated, and the right side is evaluated exactly once. Plain `=` and
  the dump forms of the shorthands stay byte-identical to v1.8.
- **in / not in**: lists (deep equality), text (substring, text-on-left only),
  dicts (keys), sets (values); chains (`a in b in c`) are refused at parse
  time.
- **round**: half away from zero — `2.5` → `3`, `-2.5` → `-3` (no banker's
  rounding surprises).
- **random(low, high)**: whole ints, both ends included, `low > high` refused.
- **sqrt(x)**: `x ** 0.5`; negatives refused: a negative number has no square root.
- **Runaway protection**: any loop over 10,000,000 steps stops itself.
- **Recursion limit**: `RecursionError` becomes a friendly JuRu error.

## The stdlib (Steps 5+6+9+12+15+16+22+23+24 — 54 reserved builtins)

The registry lives in ONE table (`src/juru/stdlib.py`): the name, its
`(min, max)` arity (max `None` = one or more) and the exact wrong-count
message. The checker and the interpreter both read it — they cannot
drift apart.

| Builtin | Does | Guard |
|---------|------|-------|
| `ask(prompt)` | read a line from the user | at most 1 argument; end-of-input is a friendly error |
| `len(x)` | length of text, a list, a dict, or a set | exactly 1 arg; text/list/dict/set only |
| `int(x)` | text or float → whole number | exactly 1 arg; rejects bool/null/list/dict/func |
| `upper(x)` | text → CAPITALS | exactly 1 arg; text only |
| `lower(x)` | text → lowercase | exactly 1 arg; text only |
| `str(x)` | anything → its text form | exactly 1 arg |
| `push(list, item)` | appends **in place**, returns the list | exactly 2 args; list first |
| `pop(list)` | remove + return the last item, in place | exactly 1 arg; a list; empty list refused |
| `insert(list, i, item)` | put item IN at `i`, the rest shifts right | exactly 3 args; a list; whole-int `i`; negative counts back, big `i` clamps |
| `remove_at(list, i)` | remove + return the item at `i` | exactly 2 args; a list; bounds-checked, `-1` = last |
| `clear(list)` | empty the list, in place | exactly 1 arg; a list |
| `extend(list, more)` | glue `more` onto the end, in place | exactly 2 args; both lists |
| `unique(list)` | a NEW list, duplicates gone (first copy wins) | exactly 1 arg; a list |
| `sum(list)` | adds the numbers (empty list → `0`) | exactly 1 arg; list of numbers only |
| `min(...)` | the smallest of one-or-more numbers, or of a list | one or more args; numbers only; empty list refused in words |
| `max(...)` | the biggest of one-or-more numbers, or of a list | one or more args; numbers only; empty list refused in words |
| `split(text, sep)` | text → list | exactly 2 args; text both; empty sep refused |
| `join(list, sep)` | list → text (readable display per item) | exactly 2 args; list + text |
| `trim(text)` | spaces/tabs/newlines off both ends | exactly 1 arg; text only |
| `replace(text, old, new)` | every `old` → `new` | exactly 3 args; text; empty `old` refused |
| `index_of(text, piece)` | first index of piece, or `-1` | exactly 2 args; text both; empty piece refused |
| `starts_with(text, prefix)` | does text begin with prefix? | exactly 2 args; text both; empty prefix refused |
| `ends_with(text, suffix)` | does text end with suffix? | exactly 2 args; text both; empty suffix refused |
| `ord(x)` | ONE character → its code number | exactly 1 arg; exactly one character |
| `chr(x)` | a code number → its character | exactly 1 arg; whole int; 0–1114111; surrogates refused |
| `abs(x)` | distance from zero | exactly 1 arg; numbers only |
| `round(x)` | nearest int, half away from zero | exactly 1 arg; numbers only |
| `random(low, high)` | one whole int, both ends included | exactly 2 args; ints; low ≤ high |
| `sqrt(x)` | the square root (float) | exactly 1 arg; numbers; x ≥ 0 |
| `sorted(list)` | a NEW sorted list (sets sort into lists) | exactly 1 arg; a list of only numbers or only text |
| `reverse(list)` | a NEW reversed list | exactly 1 arg; a list |
| `find(list, item)` | first index, or `-1` when missing | exactly 2 args; list first |
| `count(list, item)` | how many times the item appears | exactly 2 args; list first |
| `keys(dict)` | the keys as a list (insertion order) | exactly 1 arg; a dict |
| `values(dict)` | the values as a list (insertion order) | exactly 1 arg; a dict |
| `delete(dict, key)` | remove key + value, in place | exactly 2 args; a dict; missing keys are friendly errors |
| `items(dict)` | the dict as `[key, value]` pairs | exactly 1 arg; a dict |
| `merge(a, b)` | a NEW dict; `b` wins on shared keys | exactly 2 args; both dicts |
| `set_of(list)` | a set: no duplicates, first-seen order | exactly 1 arg; a list |
| `union(a, b)` | a NEW set with everything from both | exactly 2 args; both sets |
| `intersect(a, b)` | a NEW set with what is in both | exactly 2 args; both sets |
| `difference(a, b)` | a NEW set with what is in `a` but not `b` | exactly 2 args; both sets |
| `float(x)` | int/text → decimal (`float("3.5")` → `3.5`) | exactly 1 arg; bool/null/list/dict/module refused |
| `pow(a, b)` | exponents (`pow(2, 10)` → `1024`) | exactly 2 args; numbers; `0 ** negative` and negative base + fraction refused in words; huge results refused |
| `type(x)` | one word: `int`, `float`, `text`, `bool`, `null`, `list`, `dict`, `set`, `func`, `module` | exactly 1 arg; never fails |
| `help(name)` | built-in docs: no args → the whole toolbox; `"name"` → one card | at most 1 arg; non-string name refused; unknown names answer in words (never crash) |
| `sleep(seconds)` | pause the program (games love this) | exactly 1 arg; number only; no negatives; at most 30 s per call; at most 120 s per run |
| `format(text, values...)` | fill `{}` slots left to right, or `{0}`/`{1}` by index (repeats ok, `{007}` is 7); `{{`/`}}` are literal braces | one or more args; text first; mixing the two slot styles refused; missing, extra, malformed and out-of-range slots refused in words; values render like `str()`; no eval — no code ever runs from the text |
| `pad_left(text, width)` | spaces on the left up to the DISPLAY width | exactly 2 args; text + whole-int width; negative refused; at most 10000 columns; never truncates |
| `pad_right(text, width)` | spaces on the right up to the DISPLAY width | exactly 2 args; same guards as `pad_left` |
| `center(text, width)` | centered in the width; an odd extra space goes on the RIGHT | exactly 2 args; same guards as `pad_left` |
| `split_lines(text)` | multiline text → list of lines (`\n`, `\r\n`, a lone `\r`) | exactly 1 arg; text only; `""` → `[]`; a trailing newline opens no extra line; blank lines are kept |
| `join_lines(lines)` | a list of lines → one text joined with newlines | exactly 1 arg; a list of text only; `[]` → `""`; `join_lines(split_lines(t)) == t` whenever `t` has no trailing newline |

Step 22's seventeen tools add **zero keywords**; Step 23 adds exactly two
(`try`, `rescue`) plus the `fail()` builtin; Step 24 adds the six text
tools (`format`, `pad_left`, `pad_right`, `center`, `split_lines`,
`join_lines`) — still **zero keywords**. Padding measures DISPLAY width,
not `len()`: combining marks count 0, East Asian wide/fullwidth
characters count 2, everything else 1 — and no padding tool ever
truncates. Sets are list-backed
(first-seen order, ONE equality rule) and are born only from
`set_of([...])` — `{ }` stays a dict; sets refuse `+` and indexing in
words, an empty set is false, and `sorted(set)` hands back a plain list.

Purity rule: `push`, `pop`, `insert`, `remove_at`, `clear`, `extend` and
`delete` mutate; `sorted`, `reverse`, `unique` and `merge` return fresh
values and leave the original untouched (test-enforced). `find` misses
with `-1` (never a crash), and `count` counts with the same equality rules
as `==`: `1` finds `1.0`, `true` matches nothing numeric. `pow` guards
every impossible case **before** evaluating: Python would answer
`(-2) ** 0.5` with a complex number — JuRu answers in words instead.
`sleep` carries its own budget so a runaway loop cannot hide inside it,
`fail(message)` raises a user's own catchable error (kind `"fail"`, message
used verbatim), and `help` is a knowledge base of 75 cards that a test
suite keeps truthful (every example runs, every guard line matches the
real message).

Two layers guard every builtin and both print the **exact same message**
(mirror rule, test-enforced for all 54): the checker rejects a wrong arity
before a single line runs; the interpreter rejects wrong value types while
running.

## Modules (Step 7 — `import "file.jr"`)

- the module name = the file stem: `helpers.jr` → `helpers`,
  `lib/tools.jr` → `tools`; invalid stems (`my-utils.jr`) and keyword stems
  are refused at parse time
- **namespaced access** — everything the module defines lives behind the name:
  `helpers.double(21)`, `helpers.magic`; bare `double` does not leak in
- **runs exactly once** — a cache keyed by the normalized absolute path
- **checked before it runs** — the checker walks the module source first;
  errors surface as `in 'helpers.jr': <the message>` and no module code ever
  runs unchecked
- **isolated** — a module's env has no parent: it cannot see the importer's
  variables (or vice versa beyond the namespace)
- **loops detected** — a loading stack turns `a.jr → b.jr → a.jr` into
  `import loop: a.jr -> b.jr -> a.jr — a file cannot import itself, even
  through other files`
- **file-not-found is a runtime error** (the checker stays conservative and
  does not touch the filesystem): `cannot import 'x.jr' — file not found
  (looked at: <path>)`
- imports resolve next to the **running file** (`juru.py` passes its dir down)

## Templates (Step 10 — `python3 juru.py --new`)

Five small, complete starter programs live in `templates/`. The CLI copies
one into a fresh `.jr` file in the caller's directory:

| Template | Teaches |
|----------|---------|
| `starter` | variables, loops, lists — no input, deterministic output |
| `calculator` | `while` + `split` + `int` — guarded against bad math and bad input |
| `quiz` | lists + `ask` + scoring — deterministic questions |
| `guessing_game` | `random` + hints — always ends within 7 guesses |
| `word_stats` | `split` + `count` + `sorted` + `format` + `pad_right` — no input, deterministic output |

Rules of the command:

- `--new NAME` copies the `starter` template; `--new NAME TPL` picks one
- the file is written to the **caller's working directory**, never the project
- **never overwrites** — an existing `NAME.jr` (file *or* directory) is refused
- the name must be letters, digits and `_` starting with a letter (this is a
  file-name rule only; JuRu itself still accepts unicode names)
- an unknown template gets `did you mean` treatment plus the full list
- `--templates` lists every template with its description; `--version` and
  `--help` round out the CLI

The manifest in `juru.py` and the files in `templates/` must stay in sync —
a test enforces it. Every template is checker-approved and its behaviour
(exact outputs, guarded interactive sessions, guaranteed termination) is
verified end to end through the real CLI.

## The tutorial (Step 11 — `docs/tutorial.md`)

*Learn JuRu in one sitting* — seventeen chapters plus a graduation project,
from `say("hello")` to dicts, funcs, modules and the REPL. It is executable
documentation: the test suite parses every ` ```jr ` block and enforces that

- each block is semantically valid (the checker approves it — the only
  exceptions are the deliberate error demos, whose exact `JuRu Error`
  message, line and column must match what the tutorial shows)
- a block followed by a plain block prints **exactly** that output
- a block with no output block prints **nothing** (undocumented output
  would be a lie)
- `ask()` blocks are checker-only (interactive) and never claim output
- the tutorial mentions all 21 keywords, all 54 builtins, every example
  file and every template — docs cannot silently drift from the language

## Packaging (Step 13 — `pip install juru`)

The language is now a real package. Everything lives in `src/juru/`:

```
src/juru/
├── __init__.py      name + VERSION
├── lexer.py  parser.py  checker.py  interpreter.py   (relative imports)
├── cli.py           run / --new / --templates / repl / --version
├── repl.py          the interactive REPL
├── version.py       the single place the version lives
└── templates/       the 5 starter programs (shipped in the wheel)
```

- **one source of truth for the version** — `pyproject.toml` is
  `dynamic = ["version"]` and reads `juru.version.VERSION`; a test enforces it
- **the root launchers are thin** — `juru.py`, `repl.py`, `checker.py`
  bootstrap `sys.path` with `src/` and call into the package, so a clone
  still works with zero installation
- **the `juru` command** — `[project.scripts] juru = "juru.cli:main"`;
  `juru program.jr`, `juru --new NAME [TPL]`, `juru repl`,
  `juru --templates`, `juru --version` — identical behaviour to the launcher
- **templates ship in the wheel** (`package-data`), so `juru --new` works
  from any directory after a real install
- **test-enforced end to end**: a REAL wheel is built, installed into a
  fresh venv, and the installed command runs a created template program
  and the REPL (`test_packaging.py`; skips honestly if pip is absent)

## The standalone interpreter (Step 18 — one binary, no Python)

`pip` is not everyone's path, so every release also ships one frozen
executable per system — built with PyInstaller from two small files:

- `juru.spec` — the build recipe: one file, the templates for `--new`
  frozen into the bundle, console app
- `packaging/juru_entry.py` — the frozen entry point (calls
  `juru.cli.main`; kept out of the repo root so the root launcher
  `juru.py` can never shadow the package during the freeze)
- `packaging/INSTALL.txt` — rides along in every zip: quick start, PATH
  setup per platform, the macOS Gatekeeper note

Pushing a `v*` tag runs `.github/workflows/release.yml`: interpreters are
built on Windows, Linux and macOS runners, **smoke-tested as binaries**
(`--version`, run a program, piped REPL, `--new` + run the template), zipped
as `JuRu-<version>-<system>.zip`, packaged with the `.vsix`, and attached
to the GitHub release. A `Run workflow` build without a tag publishes
nothing — handy for testing a build change.

## The Python-grade setup (Step 20 — download, one step, run)

Everything a fresh user touches was made to work like Python's own
setup:

- **The REPL speaks Python's dialect.** The banner is
  `JuRu <version> (easy like Python, secure like Rust) on <platform>`
  plus a `Type "help", "exit" or "cancel"` line; the prompt is `juru>`,
  the same name as the command. A terminal command pasted into the REPL
  (`juru --version`, `pip`, `--version`, `dir`) gets a one-line nudge —
  "this is the REPL, exit first" — instead of a "'juru' was not found"
  error, while real code such as `juru = 5` still runs.
- **Real icons everywhere.** `logo/juru_icon.ico` (16→256 px, from the
  same SVG) rides inside `juru.exe` on Windows — Explorer, taskbar and
  the `.jr` file icon all show the ruby. The extension ships
  `images/juru.png` as its official icon.
- **One-step setup.** The Windows zip carries `setup.bat`: it copies the
  interpreter to `%LOCALAPPDATA%\Programs\JuRu` (Python's per-user
  spot), adds it to the user PATH, and registers `.jr` files with the
  icon and double-click run. `install.sh` does the same on
  macOS/Linux. The extension then finds the interpreter with zero
  configuration.

## The VS Code extension (Step 14 — prepare-only)

`vscode/juru-vscode/` ships everything an editor needs, ready to package:

- `package.json` — declares the `juru` language (`.jr`), the grammar and the snippets
- `syntaxes/juru.tmLanguage.json` — colors the 21 keywords, all 54 builtins,
  comments, strings, numbers and operators
- `snippets/juru.json` — `if`, `elseif`, `for`, `forin`, `while`, `func`,
  `say`, `ask`, `import`
- `language-configuration.json` — auto-closing braces/quotes, `#` comments,
  folding, indentation rules

Two guarantees, both test-enforced: the grammar's keyword alternation is
**exactly** the language's `KEYWORDS` set (highlighting can never drift),
and every JSON file is valid. Publishing to the Marketplace is a later,
separate step — `docs/vscode.md` has the two-minute load instructions.

Since Step 19 the extension is a run button, not just colors: the ▶ in
the editor title bar (and `JuRu: Run File` from the right-click menu,
the file-tree menu, Ctrl+Alt+J or the command palette) runs the open
file in a real terminal, so `ask()` works. `JuRu: Open REPL` starts a
live session. Since Step 20 the interpreter is found by itself — plain
`juru` on the PATH, or the one-step-setup location (`auto`, the setting
default) — and a missing interpreter gets a friendly dialog with a link
to the interpreter download, never a cryptic shell error.

## The REPL (Steps 5+8+16 — `python3 repl.py` or bare `juru`)

```
$ python3 repl.py
JuRu 1.6 (easy like Python, secure like Rust) on linux
Type "help", "exit" or "cancel" for more information.
type help() to see the whole toolbox
juru> 1 + 2
=> 3
juru> d = {"name": "Aman", "age": 20}
juru> d["age"] + 2
=> 22
juru> for x in [10, 20] {
....>     say(x)
....> }
10
20
juru> name = "JuRu"
juru> naame
JuRu Error (line 1, col 1): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
    naame
    ^
juru> exit
```

- one shared environment — names, lists, dicts and funcs survive line to line
- a lone expression echoes `=> value`; `say(...)` prints directly, no echo
- **bare `juru` (no arguments) opens the same REPL** — exactly like typing
  `python` with no arguments (Step 16)
- **bare `help` (or `?`) prints the whole toolbox** without needing
  parentheses — a REPL-only shortcut (Step 16)
- **multi-line blocks** — a line that ends with an open brace/paren/bracket or
  a trailing operator/keyword continues on the `....> ` prompt until the
  block closes; completion is decided by the **real lexer**, so braces inside
  text (`say("}")`) can never fool it
- an unclosed block at EOF (Ctrl-D) is a friendly error:
  `the block is not closed — '}' is missing`
- **escape hatch** — a bare `cancel` line (or Ctrl-C) drops the open block and
  starts fresh; vital when input is piped and Ctrl-C is absent
- the checker runs on every entry against the live environment (typos,
  reserved names, arity — caught before the line runs)
- dicts, `for x in`, `in`, slices, modules and all 54 builtins work in the REPL
- a mistake prints the friendly error with the line + caret (Step 17) and the
  session **continues**
- leave with `exit`, `quit`, or Ctrl-D

## Static semantic checks (Step 3 — the checker)

The checker runs AFTER parsing and BEFORE running. It catches:

1. **Typos statically** — reading a name that is never assigned anywhere gets
   the closest real name back (Step 8):
   `'naame' was not found — did you mean 'name'? (nothing with this name is
   ever assigned)` — the same suggestion drives the runtime name lookup,
   missing dict keys (`key 'naame' was not found — did you mean 'name'? …`)
   and missing module members; a hopeless typo stays plain (no wrong guess),
   and the old-Hinglish hint always wins: `'bolo' was not found (the old
   'bolo' is now 'say')`.
2. **Reserved names** — assigning to / defining any of the 54 builtins.
3. **Duplicate parameters** — `func f(a, a)` is rejected.
4. **Wrong argument counts** — for builtins always; for user funcs whenever
   the definition is unambiguous (exactly one `func` with that name).
5. **Unknown call targets** — calling a name that is never defined anywhere.
6. **Import bookkeeping** — an `import` makes its module name a known name,
   so later `module.member(...)` calls pass the conservative check.

**Conservative policy:** the checker never flags a program that could run.
If a name is assigned somewhere in the program (even inside an `if` block,
even later in the file, even as a func-local), the checker stays silent and
the interpreter guards the real run order at runtime. Zero false positives.
Member calls (`utils.f(...)`) are only checked on their **base name** — the
checker cannot see inside a module without running it, and it never runs code.

Standalone use: `python3 checker.py file.jr` → `OK — no semantic errors ✅`

## Security principles

- **No eval** — code is never built from strings.
- **null exists, the bug class doesn't** — `null == null` is safe, indexing
  through it errors cleanly.
- **Bounds checking by default** — out-of-range index = friendly error, no crash.
- **Dict keys guarded** — text/int only; missing keys error with the real key list.
- **Runaway loop protection** — 10M+ iterations stops the loop.
- **Short-circuit logic** — `false and 1/0` never divides.
- **Reserved builtins** — the 54 builtins (`ask` … `join_lines`) cannot be shadowed,
  not even as a module name (`import "len.jr"` is refused).
- **Modules are sandboxed** — isolated env, checked source, loop detection,
  one run per file, no leaking names.
- **Friendly runtime type checks** — wrong operations error with line/col.
- **GC** — the interpreter runtime's garbage collector does the work.

## Error style (example)

```
JuRu Error (line 3, col 10): missing closing " — text must be on one line
```

Since Step 17, the CLI and the REPL **show the line and point at the exact
column** — Python's caret style, in JuRu's plain words:

```
$ python3 juru.py oops.jr      # oops.jr contains: say(nums[7]) on line 2
JuRu Error (line 2, col 10): index 7 is out of range — this list has 3 items (0 to 2)
    say(nums[7])
             ^
```

The rendering rules (all test-enforced in `errfmt.py` + `test_step17.py`):

- the **message line never changes** — `str(err)` is byte-identical, so the
  checker↔interpreter mirror rule and every existing message keep holding;
  the context lines are display-only
- the caret sits under the **exact column**, computed over the raw line
  (leading indentation is stripped for display)
- **module errors** (`in 'lib.jr': ...`) borrow the module's own file for
  their context, so the caret points into the file that actually failed
- if the source is unavailable, the line is out of range, or the line is
  blank, `render()` falls back to the plain message — it can never show a
  WRONG line, and nothing ever leaks a Python traceback

Since Step 23, a runtime error that crossed a JuRu func call also records
its **JuRu call stack** at the innermost call boundary — `(func name, call
line)` pairs, user funcs only (builtins and modules do not get frames).
The display adds `called from name (line n)` lines after the caret,
innermost first. The stack is display-only: `str(err)` is unchanged, so
every existing message snapshot keeps holding, and top-level errors (no
stack at all) keep their exact old shape. Every runtime error also
carries a stable **kind** (11 documented words: `name`, `type`, `value`,
`arity`, `math`, `index`, `key`, `loop`, `input`, `file`, `fail`) — that
is what a `rescue as e` exposes as `e.kind`. Only `JuRuGalti` is ever
catchable by a rescue; host exceptions and loop signals pass through.

Old Hinglish names (`bolo`, `agar`, ...) are ordinary names now — they parse
and run; calling the old `bolo(...)` even gets a hint:
`'bolo' was not found (the old 'bolo' is now 'say')`.

## Grammar (implemented + test-verified)

```
program   → statement* EOF
statement → if | while | for | func | return | say | import | try
          | break | continue | assign | setindex | expression
assign    → NAME '=' expr
setindex  → postfix '[' expr ']' '=' expr            # a[0] = 5, d["k"] = 1
if        → 'if' expr block ('else' (if | block))?   # else if chains
while     → 'while' expr block
for       → 'for' NAME 'from' expr 'to' expr block   # for i from 1 to 10
          | 'for' NAME 'in' expr block               # for x in items
func      → 'func' NAME '(' NAME (',' NAME)* ')' block
import    → 'import' TEXT                            # "utils.jr" — parsed, module = stem
return    → 'return' expr?          (only inside func)
break     → (only inside loop)       continue → (only inside loop)
say       → 'say' '(' args ')'
try       → 'try' block 'rescue' ('as' NAME)? block   # both rescue forms
block     → '{' statement* '}'
expr      → or → and → compare → add → mul → unary → postfix → atom
or        → and ('or' and)*
and       → compare ('and' compare)*
compare   → add (('==' | '!=' | '<' | '<=' | '>' | '>=') add
               | 'in' add | 'not' 'in' add)?         # no chains — one compare per line
add       → mul (('+' | '-') mul)*                   # newline after operator = continuation
mul       → unary (('*' | '/' | '%') unary)*
unary     → ('-' | '+' | 'not') unary | postfix
postfix   → atom ('(' args ')' | '[' slice-or-index ']' | '.' NAME)*
slice     → ':' expr | expr ':' expr?                # [1:3], [2:], [:7], [:]
atom      → NUMBER | TEXT | true | false | null | NAME | '(' expr ')'
          | list | dict
list      → '[' (expr (',' expr)*)? ']'
dict      → '{' (expr ':' expr (',' expr ':' expr)*)? '}'   # keys: text or int
```

Notes:
- New lines are allowed inside `( )` and `[ ]`.
- `not` binds tighter than `and`/`or`, looser than postfix
  (`not x == y` parses as `not (x == y)`). Prefer `x not in y`.
- `{` at expression position is a dict literal (so `for i from 1 to { }`
  parses `{}` as an empty dict — the checker then refuses the value); at
  statement position it gets the friendly hint: *a dict needs a home:
  write 'data = { ... }'*.
- `a.b(...)` is a member **call**: parsed as `Call(name=b, callee=Member(a, b))`.
- `d.name` (member read) is sugar for `d["name"]`.

## The examples folders (every output exactly verified by tests)

`examples/guide/` is the beginner guide: 15 runnable lessons, one
keyword set each, covering all 21 keywords, with a full walkthrough in
`examples/README.md`. `examples/test/` holds the 15 demo programs:

| File | Shows |
|------|-------|
| `examples/test/demo.jr` | hello, text+number join, int/float math |
| `examples/test/patterns.jr` | square, triangle, pyramid star patterns |
| `examples/test/table.jr` | the 7 times table, aligned with `pad_left` |
| `examples/test/funcs_demo.jr` | factorial 1–7, fibonacci 1–10 (recursion) |
| `examples/test/lists_demo.jr` | lists, item assignment, sum |
| `examples/test/game_demo.jr` | boss battle game (while + break) |
| `examples/test/advanced_demo.jr` | FizzBuzz, primes, bubble sort, 2D grid, palindrome, countdown |
| `examples/test/number_lab.jr` | primes, perfect numbers, digit reversal, gcd/lcm |
| `examples/test/algo_lab.jr` | selection sort, binary search, dedupe, RLE, longest word |
| `examples/test/game_lab.jr` | tic-tac-toe with winner check + the arena fight |
| `examples/test/stdlib_demo.jr` | the builtin toolbox in action |
| `examples/test/mega_demo.jr` | school report: grades, bubble sort, topper, histogram |
| `examples/test/dicts_demo.jr` | word counting with dicts + `for x in` |
| `examples/test/helpers.jr` | a tiny module (import me from another file) |
| `examples/test/import_demo.jr` | modules: namespace, run-once caching |

## Roadmap

| Step | What | Status |
|------|------|--------|
| 1 | Design + Lexer (text → tokens) | ✅ DONE — 55 tests |
| 2 | Parser (tokens → AST) + parse-time checks | ✅ DONE — 111 tests |
| 3 | Semantic checker (catches mistakes before running) | ✅ DONE — 47 tests |
| 4 | Interpreter (run the code) | ✅ DONE — 93 tests + demos verified |
| 5 | Stdlib (builtins) + REPL + more examples | ✅ DONE — stdlib 25, REPL 10, programs 13, mega 14 |
| 6 | Dicts, `for x in`, `in`/`not in`, slices, string + math stdlib | ✅ DONE — 46 tests |
| 7 | Modules: `import`, namespaces, run-once, isolation, loop detection | ✅ DONE — 17 tests |
| 8 | Did-you-mean + the multi-line REPL (`....> `, cancel) | ✅ DONE — 19 tests |
| 9 | Stdlib wave 2: sorted, reverse, find, keys, values, count | ✅ DONE — 23 tests |
| 10 | Templates: 5 starter programs + `--new`/`--templates` CLI | ✅ DONE — 24 tests |
| 11 | The tutorial: docs/tutorial.md, executable and test-enforced | ✅ DONE — 11 tests |
| 12 | Stdlib wave 3: float, pow, pop, type (the input/math wave) | ✅ DONE — 22 tests |
| 13 | pip packaging: src/juru/ + pyproject.toml + `juru` command | ✅ DONE — 9 tests |
| 14 | VS Code extension (prepare-only, files + docs ready) | ✅ DONE — 3 tests |
| 15 | `help()` — the built-in docs: 48 truthful cards, aliases, did-you-mean | ✅ DONE — 15 tests |
| 16 | `sleep(seconds)` + the bare-`juru` REPL + REPL `help`/`?` | ✅ DONE — 13 tests |
| 17 | Python-style error display: the line + a caret under the exact column | ✅ DONE — 10 tests |
| 18 | Standalone interpreter: PyInstaller spec → release zips, no Python needed | ✅ DONE — release workflow |
| 19 | VS Code run button + REPL command + `juru.interpreterPath` | ✅ DONE — 3 tests |
| 20 | Distribution polish — Python-grade REPL, real icons, one-step setup | ✅ DONE — 5 tests |
| 21 | A beginner guide: one runnable lesson per keyword, all linked | ✅ DONE — 4 tests |
| 22 | Collections & ergonomics wave 1: aug-assign, negative indexing, slice steps, 17 collection builtins, sets, the stdlib registry | ✅ DONE — 71 tests |
| 23 | Errors you can catch: `try`/`rescue`, the `fail()` builtin, 11 documented error kinds, JuRu call stacks in error displays | ✅ DONE — 56 tests |
| 24 | Text & formatting wave: `format()`, `pad_left`/`pad_right`/`center`, `split_lines`/`join_lines` — six builtins, zero new keywords | ✅ DONE — 24 tests |
| — | Ultimate torture: steps 1–23 combined | ✅ DONE — 56 tests |
| — | **Total: 784 tests green** | |

After 23 the language, its distribution, its setup and its on-ramp are
complete, the way Python's is: download, one setup step, run — and a
guide that teaches every keyword. Still open, all optional and on
demand: publishing the extension to the Marketplace, a docs website,
and a stdlib wave 4 beyond `help`/`sleep` (only when a real use asks
for it).
