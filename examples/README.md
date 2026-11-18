# The JuRu Beginner Guide

Welcome! This guide teaches you the **whole language** in 15 small,
runnable lessons — one keyword at a time. JuRu has exactly **21
keywords**, and every single one of them gets its own lesson here.
Read one lesson, run its file, change a line, run it again. That is
the whole method.

> JuRu = easy (easier than Python) + secure (safe like Rust).
> Files end in `.jr`, code reads like plain English, and the computer
> helps you when you make a mistake.

---

## How to run a lesson

From the top of the JuRu repository (the folder with `juru.py`):

```bash
python3 juru.py examples/guide/00_start_here.jr
```

If you installed JuRu with the setup (or with pip), the shorter form
works from anywhere:

```bash
juru examples/guide/00_start_here.jr
```

Every lesson prints its output and stops. Nothing asks you questions,
nothing is random — you can rerun a lesson a hundred times and it
says the same thing a hundred times. Change a number, rerun, watch
what happens. That is how you learn a language.

**Tip:** make a mistake on purpose once — type a name wrong, delete a
closing brace — and read the friendly error. Errors are teachers too.

---

## The lessons

| # | Lesson | Keywords it teaches | In one line |
|---|--------|---------------------|-------------|
| 00 | [00_start_here.jr](guide/00_start_here.jr) | — (variables + `say`) | your first minutes: names, values, running |
| 01 | [01_say.jr](guide/01_say.jr) | `say` | make the computer talk |
| 02 | [02_if_else.jr](guide/02_if_else.jr) | `if`, `else` | let the program decide |
| 03 | [03_while.jr](guide/03_while.jr) | `while` | repeat while something is true |
| 04 | [04_counting.jr](guide/04_counting.jr) | `for`, `from`, `to` | count for me, both ends included |
| 05 | [05_for_in.jr](guide/05_for_in.jr) | `for`, `in` | walk through a list, item by item |
| 06 | [06_break.jr](guide/06_break.jr) | `break` | stop the loop right now |
| 07 | [07_continue.jr](guide/07_continue.jr) | `continue` | skip this round, keep going |
| 08 | [08_func.jr](guide/08_func.jr) | `func` | give a piece of code a name |
| 09 | [09_return.jr](guide/09_return.jr) | `return` | hand a value back to the caller |
| 10 | [10_booleans.jr](guide/10_booleans.jr) | `true`, `false`, `null` | yes, no, and "nothing yet" |
| 11 | [11_logic.jr](guide/11_logic.jr) | `and`, `or`, `not` | combine questions into one decision |
| 12 | [12_membership.jr](guide/12_membership.jr) | `in`, `not in` | is it inside? (lists, dicts, text) |
| 13 | [13_import.jr](guide/13_import.jr) | `import` | use code from another file |
| 14 | [14_try.jr](guide/14_try.jr) | `try`, `rescue` | catch errors so the show goes on |
| — | [tools.jr](guide/tools.jr) | — | the little module lesson 13 imports |

That is the complete language: 21 keywords, 15 lessons, no hidden
extras. (JuRu also has 48 builtins — ready-made tools like `len`,
`split`, `sorted`, `fail` — and the REPL's `help()` lists them all.)

---

## Lesson 00 — Start here

**File:** [guide/00_start_here.jr](guide/00_start_here.jr)

Two ideas every program is built from: a value gets a name (a
variable), and the computer shows it (`say`). Text joins numbers for
free — no converting, no ceremony.

```jr
name = "Ada"
age = 12
say("Hello, " + name + "!")      # Hello, Ada!
say("You are " + age + " years old.")   # You are 12 years old.
```

```text
Hello, Ada!
You are 12 years old.
5
2.5
Next year: 13
```

## Lesson 01 — say

**File:** [guide/01_say.jr](guide/01_say.jr) — keyword: `say`

`say(...)` shows one thing on its own line. The part inside is
computed first, so `say(2 + 2)` prints `4`. Text + number joins
automatically.

```text
JuRu talks to you
42
3.5
4
22
the answer is 42
abc
Hello, Ada!
```

## Lesson 02 — if / else

**File:** [guide/02_if_else.jr](guide/02_if_else.jr) — keywords: `if`, `else`

The block in `{ }` runs only when the condition is true. `else if`
chains more questions; `else` catches what is left. Only ONE branch
ever runs.

```jr
if score >= 90 {
    say("grade A")
} else if score >= 75 {
    say("grade B")
} else {
    say("keep practicing")
}
```

```text
keep practicing
welcome in
that was never the password
```

## Lesson 03 — while

**File:** [guide/03_while.jr](guide/03_while.jr) — keyword: `while`

Repeat as long as the condition stays true. Something inside the
block must move it toward false — that is what ends the loop.

```text
T-minus 5
T-minus 4
T-minus 3
T-minus 2
T-minus 1
Lift off!
pocket money: 128
```

## Lesson 04 — for, from, to

**File:** [guide/04_counting.jr](guide/04_counting.jr) — keywords: `for`, `from`, `to`

`for i from 1 to 5` counts 1, 2, 3, 4, 5 — **both ends included**.
The counting variable is a real variable you can use in the body.

```text
day 1
day 2
day 3
day 4
day 5
9 o'clock
10 o'clock
11 o'clock
12 o'clock
1+2+...+10 = 55
```

## Lesson 05 — for ... in

**File:** [guide/05_for_in.jr](guide/05_for_in.jr) — keywords: `for`, `in`

Walking a list needs no index bookkeeping: `for x in items` hands you
one item per round. `len` counts, `[0]` picks.

```text
I like apple
I like banana
I like cherry
total: 26
first fruit: apple
we have 3 fruits
```

## Lesson 06 — break

**File:** [guide/06_break.jr](guide/06_break.jr) — keyword: `break`

Stop the loop **right now**, jump out, continue after it. Classic
use: search until you find the thing, then stop looking.

```text
found a great score: 9
code cracked after 6 tries
search over
```

## Lesson 07 — continue

**File:** [guide/07_continue.jr](guide/07_continue.jr) — keyword: `continue`

Skip the rest of **this round only** — the loop itself goes on.
`break` leaves the loop; `continue` leaves one round.

```text
odd number: 1
odd number: 3
odd number: 5
odd number: 7
ate the apple
ate the banana
ate the cherry
```

## Lesson 08 — func

**File:** [guide/08_func.jr](guide/08_func.jr) — keyword: `func`

Write a piece of code once, give it a name, call it as often as you
like with different values. Several arguments? Separate them with
commas.

```text
Go Red!
Go Blue!
Go Gold!
The cow says moo
The cat says meow
hello!
```

## Lesson 09 — return

**File:** [guide/09_return.jr](guide/09_return.jr) — keyword: `return`

`return` sends a value back to whoever called the func — the call
itself becomes that value. `return` also ends the func immediately,
which makes guard clauses easy.

```text
21
answer: 16
true
false
5.0
0
```

## Lesson 10 — true, false, null

**File:** [guide/10_booleans.jr](guide/10_booleans.jr) — keywords: `true`, `false`, `null`

`true` and `false` are the two answers to every yes/no question.
`null` means "nothing yet" — an empty box you will fill later.

```text
true
false
null
gold
bool
null
float
true
false
true
still searching...
the map
```

## Lesson 11 — and, or, not

**File:** [guide/11_logic.jr](guide/11_logic.jr) — keywords: `and`, `or`, `not`

Real decisions combine questions: `and` needs both sides, `or` needs
one, `not` flips. The whole truth table is four rows — the lesson
prints it.

```text
you can enter
weekend!
no umbrella needed
false
true
false
true
true
```

## Lesson 12 — in, not in

**File:** [guide/12_membership.jr](guide/12_membership.jr) — keywords: `in`, `not`

The same word `in` asks "is it inside?" about three different things:
a **list** (one of the items?), a **dict** (one of the keys?), a
**text** (part of the text?). `not in` asks the opposite.

```text
green is in the list
pink is missing
ada's age: 12
hello contains ell
hello has no z
```

## Lesson 13 — import

**File:** [guide/13_import.jr](guide/13_import.jr) — keyword: `import`

`import "tools.jr"` runs another file **once** and gives you its
funcs and values through the module `tools` — the module name is the
file name. Imports always look next to the file that imports them,
which is why [tools.jr](guide/tools.jr) lives right here.

```text
hello Ada!
42
magic number: 42
100
```

That was keyword number 19. One lesson left — the two newest words
in the language.

---

## Lesson 14 — try / rescue

**File:** [guide/14_try.jr](guide/14_try.jr) — keywords: `try`, `rescue`

Real programs meet failure: text that is not a number, a list index
past the end, a missing dict key. `try { ... }` runs risky code; the
moment a JuRu error happens, JuRu jumps to the `rescue` instead of
stopping the program. The caught error is a value: `e.message`,
`e.kind`, `e.line`, `e.col`. `fail(message)` raises your own error —
the nearest rescue catches it.

```text
caught: int('not a number') — 'not a number' is not a whole number
the program is still alive
kind:   index
detail: index 99 is out of range — this list has 3 items (0 to 2)
no bob here — moving on
12
fail: age cannot be negative
```

That was keyword number 20 and 21 — **you have now seen every keyword
JuRu has.** 🎉

---

## The demo programs (`examples/test/`)

Fifteen complete, verified programs live in
[examples/test/](test/) — bigger than the lessons, every output
checked by the test suite. Read them, run them, then bend them.

| File | Shows |
|------|-------|
| [test/demo.jr](test/demo.jr) | hello, text+number join, int/float math |
| [test/patterns.jr](test/patterns.jr) | square, triangle, pyramid star patterns |
| [test/table.jr](test/table.jr) | the 7 times table |
| [test/funcs_demo.jr](test/funcs_demo.jr) | factorial 1–7, fibonacci 1–10 (recursion) |
| [test/lists_demo.jr](test/lists_demo.jr) | lists, item assignment, sum |
| [test/game_demo.jr](test/game_demo.jr) | boss battle game (while + break) |
| [test/advanced_demo.jr](test/advanced_demo.jr) | FizzBuzz, primes, bubble sort, 2D grid, palindrome |
| [test/number_lab.jr](test/number_lab.jr) | primes, perfect numbers, digit reversal, gcd/lcm |
| [test/algo_lab.jr](test/algo_lab.jr) | selection sort, binary search, dedupe, RLE |
| [test/game_lab.jr](test/game_lab.jr) | tic-tac-toe with winner check + the arena fight |
| [test/stdlib_demo.jr](test/stdlib_demo.jr) | the builtin toolbox in action |
| [test/mega_demo.jr](test/mega_demo.jr) | school report: grades, ranking, topper, histogram |
| [test/dicts_demo.jr](test/dicts_demo.jr) | word counting with dicts + `for x in` |
| [test/helpers.jr](test/helpers.jr) | a tiny module (import me from another file) |
| [test/import_demo.jr](test/import_demo.jr) | modules: namespace, run-once caching |

Run any of them the same way:

```bash
python3 juru.py examples/test/game_demo.jr
```

---

## What next?

- The full tutorial, zero to confident:
  [docs/tutorial.md](../docs/tutorial.md)
- The whole language on one page: [docs/syntax.md](../docs/syntax.md)
- Ask the REPL: `python3 repl.py`, then `help()` — and `help("split")`
  for any tool's card.
- Want a project skeleton? `juru --new mygame guessing_game` (five
  templates: `starter`, `calculator`, `quiz`, `guessing_game`,
  `word_stats`).

Have fun — the language is small on purpose, so you can keep all of
it in your head. 🚀
