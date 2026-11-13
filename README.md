<p align="center">
  <img src="logo/juru_icon.svg" width="180" alt="JuRu logo — a ruby cut from Jupyter orange and Ruby red, with curly braces carved in">
</p>

# JuRu

> **JuRu** = easy (easier than Python) + secure (safe like Rust).
> **File extension: `.jr`** — run it like `python file.py`: `python3 juru.py program.jr`

`19 keywords · 24 builtins · 5 templates · 15 examples · 542 tests green · version 1.3 (see version.py) · MIT`

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

# 3) try the live REPL
python3 repl.py

# 4) or start from a ready-made template
python3 juru.py --new mygame guessing_game
python3 juru.py mygame.jr
```

REPL session:

```
JuRu 1.3 REPL — full English, easy like Python, secure like Rust.
type 'exit' or press Ctrl-D to leave
type 'cancel' or press Ctrl-C to drop an open block
jruru> 1 + 2
=> 3
jruru> d = {"name": "Aman", "age": 20}
jruru> d["age"] + 2
=> 22
jruru> for x in [10, 20] {          ← blocks can span lines now
......>     say(x)
......> }
10
20
jruru> sorted([3, 1, 2])
=> [1, 2, 3]
jruru> count(["go", "go", "stop"], "go")
=> 2
jruru> name = "JuRu"
jruru> naame                         ← a typo? it helps you
JuRu Error (line 1, col 1): 'naame' was not found — did you mean 'name'?
                                     (nothing with this name is ever assigned)
jruru> exit
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
and a typo gets the closest real name back:

```
JuRu Error (line 3, col 10): missing closing " — text must be on one line
JuRu Error (line 5, col 9): index 7 is out of range — this list has 3 items (0 to 2)
JuRu Error (line 2, col 1): 'break' only works inside a loop (for / while)
JuRu Error (line 4, col 14): key 'z' was not found — this dict has: a, b
JuRu Error (line 1, col 1): cannot import 'ghost.jr' — file not found (looked at: /tmp/ghost.jr)
JuRu Error (line 2, col 5): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
JuRu Error (line 1, col 5): 'bolo' was not found (the old 'bolo' is now 'say')
```

## Keywords (19)

```
say   if    else    while   for    from    to      in
break continue func    return  true   false   null
and   or    not     import
```

`else if` is two words. Blocks are `{ }` — no indentation headaches.
One statement per line; comments start with `#`.

## Builtins (24 — all reserved names)

| Builtin | Does |
|---------|------|
| `ask(prompt)` | read a line from the user |
| `len(x)` | length of text, a list, or a dict |
| `int(x)` | text/float → whole number (`int("42")` → `42`, `int(2.9)` → `2`) |
| `upper(x)` | text → CAPITALS |
| `lower(x)` | text → lowercase |
| `str(x)` | anything → text (`str(2.5)` → `"2.5"`) |
| `push(list, item)` | append in place, returns the list |
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

Only `push` changes a list in place — `sorted` and `reverse` hand you a fresh
list and leave the original alone. No new keywords were added for these six:
the language stays 19 keywords big.

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
| `calculator` | `--new calc calculator` | `while` + `split` + input |
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
.jr file → lexer.py → parser.py → checker.py → interpreter.py → output
              tokens      AST         semantic         runs your code
                                        ok?

repl.py      same pipeline, one line at a time, one shared environment
```

- **lexer** — text → tokens (unicode names welcome, Devanagari included)
- **parser** — tokens → AST + parse-time safety (`break` outside a loop dies here)
- **checker** — semantic checks **before** a single line runs: typos,
  reserved names, wrong argument counts, unknown calls — **including inside
  every imported module**
- **interpreter** — runs the AST with guards: bounds checks, runaway-loop
  protection, short-circuit logic, friendly recursion limits

## Tests — 542, all green

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
python3 test_templates.py     # 24   (the 5 templates + --new/--templates CLI)
python3 test_tutorial.py      # 11   (docs/tutorial.md cannot lie)
python3 test_ultimate.py      # 34   (steps 1–11 combined, no mercy)
```

## Project structure

```
JuRu/
├── lexer.py            # source → tokens
├── parser.py           # tokens → AST (+ dump() for the S-expression view)
├── checker.py          # semantic checks (runs before anything executes)
├── interpreter.py      # the runner + the stdlib + modules
├── juru.py             # the CLI runner (wires the whole pipeline)
├── repl.py             # the interactive REPL
├── version.py          # the single place the version lives
├── templates/          # 5 ready-made starter programs (--new copies them)
├── design.md           # the full design document
├── docs/tutorial.md    # learn JuRu in one sitting (test-verified)
├── docs/syntax.md      # the A to Z cheat sheet
├── logo/juru_icon.svg  # the language icon (orange → red ruby + braces)
├── examples/           # 15 verified demo programs
├── test_*.py           # 15 test suites, 542 tests
└── LICENSE             # MIT
```

## Docs

- `docs/tutorial.md` — learn JuRu in one sitting (every block test-verified)
- `design.md` — the full design: semantics, grammar, security principles
- `docs/syntax.md` — the A to Z language cheat sheet

## License

MIT — see [LICENSE](LICENSE).
