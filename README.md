<p align="center">
  <img src="logo/juru_icon.svg" width="180" alt="JuRu logo — a ruby cut from Jupyter orange and Ruby red, with curly braces carved in">
</p>

# JuRu

> **JuRu** = easy (easier than Python) + secure (safe like Rust).
> **File extension: `.jr`** — run it like `python file.py`: `python3 juru.py program.jr`

`19 keywords · 30 builtins · 5 templates · 15 examples · 627 tests green · version 1.6 (see version.py) · MIT`

---

## Why JuRu?

1. **Easy** — few keywords, plain English, human error messages, zero setup.
2. **Conversation feel** — reading code feels like talking:
   `say(...)`, `if ... else`, `for i from 1 to 10`, `for x in items`, `func add(a, b)`.
3. **Secure by design** — every list index bounds-checked, loops that run away
   stop themselves, builtins can never be shadowed, no eval, no null-bug class,
   and mistakes are caught **before** the program runs.

## Quickstart

```bash
# 1) run a program
python3 juru.py examples/demo.jr
# hello JuRu!
# Level 3
# 8
# 2.5
# 1
# 5.0
# 5.0

# 2) write your own (any file ending in .jr)
echo 'say("hello JuRu!")' > hello.jr
python3 juru.py hello.jr

# 3) try the live REPL (or just `python3 juru.py` — same thing, like `python`)
python3 repl.py

# 4) or start from a ready-made template
python3 juru.py --new mygame guessing_game
python3 juru.py mygame.jr
```

REPL session:

```
JuRu 1.6 (easy like Python, secure like Rust) on win32
Type "help", "exit" or "cancel" for more information.
type help() to see the whole toolbox
juru> 1 + 2
=> 3
juru> help("pow")                   ← built-in docs, like Python's help()
pow(a, b)

raise a to the power b — the exponent tool (no ** to memorize).
...
juru> d = {"name": "Aman", "age": 20}
juru> d["age"] + 2
=> 22
juru> for x in [10, 20] {          ← blocks can span lines now
....>     say(x)
....> }
10
20
juru> sorted([3, 1, 2])
=> [1, 2, 3]
juru> count(["go", "go", "stop"], "go")
=> 2
juru> name = "JuRu"
juru> naame                         ← a typo? it helps you
JuRu Error (line 1, col 1): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
    naame
    ^
juru> exit
```

## The language in 30 seconds

```python
# hello.jr — everything you need on one screen
name = "JuRu"                       # variables, no declarations
say("hello " + name + "!")          # text joins anything: "hello JuRu!"

if 5 > 2 and not false {
    say("logic works")
} else {
    say("something is very wrong")
}

for i from 1 to 5 {                 # `to` is included: 1 2 3 4 5
    say(i)
}

nums = [3, 1, 4, 1, 5]              # lists, item assignment
nums[0] = 30
push(nums, 9)                       # appends in place
say(nums)                           # [30, 1, 4, 1, 5, 9]
say(sum(nums))                      # 50

person = {"name": "Aman", "age": 20}    # dicts: text or whole-number keys
say(person["name"])                     # Aman
say(person.name)                        # Aman (dot sugar for reading)
for key in person { say(key) }          # for-in walks the keys

say("ell" in "hello")               # true — `in` works on text, lists, dicts
say(nums[1:3])                      # slices: [1, 4] — never crash, they clamp
say(upper(trim("  hi  ")))          # string tools: HI

import "helpers.jr"                 # modules: another .jr file, run once
say(helpers.double(21))             # 42 — namespaced: helpers.name

func factorial(n) {                 # funcs + recursion
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}
say(factorial(5))                   # 120
```

Every mistake gets a human message, with the exact line and column —
and since version 1.5 the CLI and the REPL also show the offending line
with a caret under the exact character, like Python. A typo even gets
the closest real name back:

```
JuRu Error (line 3, col 10): missing closing " — text must be on one line
JuRu Error (line 5, col 9): index 7 is out of range — this list has 3 items (0 to 2)
JuRu Error (line 2, col 1): 'break' only works inside a loop (for / while)
JuRu Error (line 4, col 14): key 'z' was not found — this dict has: a, b
JuRu Error (line 1, col 1): cannot import 'ghost.jr' — file not found (looked at: /tmp/ghost.jr)
JuRu Error (line 2, col 5): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
JuRu Error (line 1, col 5): 'bolo' was not found (the old 'bolo' is now 'say')
```

```text
$ python3 juru.py oops.jr            # oops.jr: nums = [1, 2, 3] / say(nums[7])
JuRu Error (line 2, col 10): index 7 is out of range — this list has 3 items (0 to 2)
    say(nums[7])
             ^
```

## Keywords (19)

```
say   if    else    while   for    from    to      in
break continue func    return  true   false   null
and   or    not     import
```

`else if` is two words. Blocks are `{ }` — no indentation headaches.
One statement per line; comments start with `#`.

## Builtins (30 — all reserved names)

| Builtin | Does |
|---------|------|
| `ask(prompt)` | read a line from the user |
| `len(x)` | length of text, a list, or a dict |
| `int(x)` | text/float → whole number (`int("42")` → `42`, `int(2.9)` → `2`) |
| `float(x)` | text/int → decimal (`float("3.5")` → `3.5`, `float(5)` → `5.0`) |
| `upper(x)` | text → CAPITALS |
| `lower(x)` | text → lowercase |
| `str(x)` | anything → text (`str(2.5)` → `"2.5"`) |
| `push(list, item)` | append in place, returns the list |
| `pop(list)` | remove and return the last item, in place (empty → friendly error) |
| `sum(list)` | add the numbers (empty list → `0`) |
| `min(a, b)` / `max(a, b)` | the smaller / bigger number |
| `split(text, sep)` | text → list (`split("a,b", ",")` → `[a, b]`) |
| `join(list, sep)` | list → text (`join([1, 2], "-")` → `1-2`) |
| `trim(text)` | drop spaces/tabs/newlines from both ends |
| `replace(text, old, new)` | swap every `old` for `new` |
| `abs(x)` | distance from zero (`abs(-5)` → `5`) |
| `round(x)` | nearest whole number, half away from zero (`2.5` → `3`, `-2.5` → `-3`) |
| `random(low, high)` | one whole number, both ends included |
| `sqrt(x)` | square root (`sqrt(9)` → `3.0`) |
| `sorted(list)` | a NEW sorted list — numbers or text, never mutates |
| `reverse(list)` | a NEW reversed list — never mutates |
| `find(list, item)` | first index of the item, or `-1` when it is not there |
| `keys(dict)` | the dict's keys as a list, in insertion order |
| `values(dict)` | the dict's values as a list, in insertion order |
| `count(list, item)` | how many times the item appears (deep equality) |
| `pow(a, b)` | exponents without `**` (`pow(2, 10)` → `1024`); impossible math is refused in words |
| `type(x)` | one word: `int`, `float`, `text`, `bool`, `null`, `list`, `dict`, `func`, `module` |
| `help(name)` | built-in docs — `help()` lists the whole toolbox, `help("pow")` prints one card |
| `sleep(seconds)` | pause the program (`sleep(1)` waits one second) — at most 30 s per call, 120 s per run |

Only `push` and `pop` change a list in place — `sorted` and `reverse` hand
you a fresh list and leave the original alone. Waves 3–4 (`float`, `pow`,
`pop`, `type`, then `help`, `sleep`) added **zero** new keywords: the
language stays 19 keywords big. And `help("anything")` never lies — a
test suite runs every card's examples and checks its guard lines against
the real error messages.

## Templates — start in one command

Five small, complete programs, ready to copy and make yours:

```bash
python3 juru.py --new hello                # starter template (the default)
python3 juru.py --new calc calculator      # pick a template by name
python3 juru.py --templates                # list them all
```

| Template | Start it with | What it teaches |
|----------|---------------|-----------------|
| `starter` | `--new hello` | variables, loops, lists |
| `calculator` | `--new calc calculator` | `while` + `split` + `int`/`float` + input |
| `quiz` | `--new myquiz quiz` | lists + `ask` + scoring |
| `guessing_game` | `--new game guessing_game` | `random` + hints |
| `word_stats` | `--new stats word_stats` | `split` + `count` + `sorted` |

`--new` never overwrites an existing file and refuses nuisance names —
every refusal is a friendly, one-line explanation. The new tutorial
([docs/tutorial.md](docs/tutorial.md)) walks you from zero to this table.

## Examples (every output exactly verified by tests)

| File | Shows |
|------|-------|
| `examples/demo.jr` | hello, text+number join, int/float math |
| `examples/patterns.jr` | square, triangle, pyramid star patterns |
| `examples/table.jr` | the 7 times table |
| `examples/funcs_demo.jr` | factorial 1–7, fibonacci 1–10 (recursion) |
| `examples/lists_demo.jr` | lists, item assignment, sum |
| `examples/game_demo.jr` | boss battle game (while + break) |
| `examples/advanced_demo.jr` | FizzBuzz, primes, bubble sort, 2D grid, palindrome |
| `examples/number_lab.jr` | primes, perfect numbers, digit reversal, gcd/lcm |
| `examples/algo_lab.jr` | selection sort, binary search, dedupe, RLE |
| `examples/game_lab.jr` | tic-tac-toe with winner check + the arena fight |
| `examples/stdlib_demo.jr` | the builtin toolbox in action |
| `examples/mega_demo.jr` | school report: grades, ranking, topper, histogram |
| `examples/dicts_demo.jr` | word counting with dicts + `for x in` |
| `examples/helpers.jr` | a tiny module (import me from another file) |
| `examples/import_demo.jr` | modules: namespace, run-once caching |

## How it works (the pipeline, all connected)

```
.jr file → lexer → parser → checker → interpreter → output
            tokens    AST      semantic    runs your code
                               ok?

repl        same pipeline, one line at a time, one shared environment
```

(all in the `src/juru/` package; the root launchers wire it up)

- **lexer** — text → tokens (unicode names welcome, Devanagari included)
- **parser** — tokens → AST + parse-time safety (`break` outside a loop dies here)
- **checker** — semantic checks **before** a single line runs: typos,
  reserved names, wrong argument counts, unknown calls — **including inside
  every imported module**
- **interpreter** — runs the AST with guards: bounds checks, runaway-loop
  protection, short-circuit logic, friendly recursion limits
- **helpdb** — the `help()` knowledge base: one truthful card per builtin
  and keyword, aliases (`power` → `pow`), did-you-mean for unknown names
- **errfmt** — error display: the message line plus the offending source
  line and a caret under the exact column (CLI + REPL)

## Install it

**Option 1 — download the interpreter (no Python needed).** From the
[releases page](https://github.com/RaviHackjr/JuRu/releases), grab the
zip for your system and let its setup do the rest:

- **Windows** — unzip, double-click **setup.bat**, open a new terminal.
  It installs the interpreter to `%LOCALAPPDATA%\Programs\JuRu` (like
  Python's per-user install), puts it on your PATH, and gives `.jr`
  files the JuRu icon in Explorer. Done — no admin, no settings.
- **macOS / Linux** — unzip, `sh install.sh` (it picks a bin folder and
  tells you if one PATH line remains).

Then it is just Python's flow:

```bash
juru --version              # JuRu 1.6
juru hello.jr               # run it
juru                        # bare command → the REPL (exactly like `python`)
```

**Option 2 — pip (needs Python 3.9+).** The whole language is a pip
package — `src/juru/`, one flat namespace:

```bash
pip install juru            # same interpreter, as a package
juru --new hello            # starter template
juru repl                   # try ideas live
```

**Option 3 — from a clone.** Nothing changes: `python3 juru.py program.jr`,
`python3 repl.py` and `python3 checker.py file.jr` all work in place —
they are thin launchers into the same package.

Full walkthrough with every platform detail:
[docs/install.md](docs/install.md).

## VS Code (official, ready to load)

Syntax highlighting (all 19 keywords + 30 builtins), snippets, brackets,
folding, and the run button — the extension lives at
`vscode/juru-vscode/`, finds the interpreter by itself (nothing to
configure), and its keyword list is test-enforced against the language.
Load it in two minutes:

```bash
cd vscode/juru-vscode
npx --yes @vscode/vsce package --no-dependencies
code --install-extension juru-vscode-1.6.0.vsix
```

Full guide: [docs/vscode.md](docs/vscode.md). (Prepare-only — the
Marketplace upload is a later, separate step.)

## Tests — 627, all green

```bash
python3 test_lexer.py         # 55
python3 test_parser.py        # 111
python3 test_checker.py       # 47
python3 test_interpreter.py     # 93
python3 test_programs.py      # 13   (3 heavy programs, exact output)
python3 test_stdlib.py        # 25
python3 test_repl.py          # 10
python3 test_mega.py          # 14   (the combined torture test)
python3 test_step6.py         # 46   (dicts, for-in, in/not-in, slices, strings, math)
python3 test_step7.py         # 17   (modules: import, run-once, loops, isolation)
python3 test_step8.py         # 19   (did-you-mean + the multi-line REPL)
python3 test_step9.py         # 23   (sorted/reverse/find/keys/values/count)
python3 test_step12.py        # 22   (float/pow/pop/type + all their guards)
python3 test_step15.py        # 15   (help(): truthful cards, aliases, unknowns)
python3 test_step16.py        # 13   (sleep() guards + the bare-`juru` REPL)
python3 test_step17.py        # 10   (line + caret error display)
python3 test_templates.py     # 24   (the 5 templates + --new/--templates CLI)
python3 test_tutorial.py      # 11   (docs/tutorial.md cannot lie)
python3 test_packaging.py     # 9    (real wheel → venv install → juru command)
python3 test_ultimate.py      # 50   (steps 1–20 combined, no mercy)
```

## Project structure

```
JuRu/
├── juru.py             # thin launcher → src/juru/cli.py (run/--new/repl)
├── repl.py             # thin launcher → src/juru/repl.py
├── checker.py          # thin launcher → src/juru/checker.py (check a file)
├── pyproject.toml      # pip packaging (pip install juru)
├── juru.spec           # PyInstaller spec — the standalone interpreter
├── packaging/          # the frozen entry point + files that ride in the zips
├── src/juru/           # the package: lexer, parser, checker, interpreter,
│                       #   cli, repl, helpdb, errfmt, version + templates/
├── vscode/juru-vscode/  # the official VS Code extension (prepare-only)
├── design.md           # the full design document
├── CHANGELOG.md        # what changed in every version
├── docs/tutorial.md    # learn JuRu in one sitting (test-verified)
├── docs/syntax.md      # the A to Z cheat sheet
├── docs/install.md     # every way to install, per platform
├── docs/vscode.md      # load the extension in 2 minutes
├── logo/               # the icon set: juru_icon.svg (source),
│                       #   juru_icon.ico (16→256 px, inside juru.exe)
├── examples/           # 15 verified demo programs
├── test_*.py           # 20 test suites, 627 tests
└── LICENSE             # MIT
```

## Docs

- `docs/tutorial.md` — learn JuRu in one sitting (every block test-verified)
- `design.md` — the full design: semantics, grammar, security principles
- `docs/syntax.md` — the A to Z language cheat sheet

## License

MIT — see [LICENSE](LICENSE).
