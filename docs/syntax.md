# JuRu Syntax — The A to Z Cheat Sheet

> **File extension: `.jr`** (like `.py` for Python, `.c` for C — ours is `.jr`)
> **How to run:** `python3 juru.py program.jr`
> **Try it live:** `python3 repl.py`
>
> The idea behind JuRu: code should feel like a **conversation in plain English**.
> Only 19 keywords — and they cover everything.

---

## 1. `say` — show something

```
say("hello")            # hello
say("Level " + 3)       # Level 3   ← the number joins automatically
say(1, 2, "ok")         # 1 2 ok (joined with spaces)
say()                   # an empty line
```

## 2. Variables — keeping things

```
name = "Aman"
age = 20
height = 5.9
ready = true
nothing = null
```

## 3. Data types (all automatic — no declarations, no juggling)

| Type | Example |
|------|---------|
| int (whole number) | `10`, `-5` |
| float (decimal) | `3.14`, `10 / 4` |
| text (string) | `"hello"` |
| bool | `true`, `false` |
| list | `[1, "two", 3.0]` |
| dict | `{"name": "Aman", 1: "one"}` |
| null (nothing) | `null` |

int + float = float **automatically** (`1 + 2.5` → `3.5`). No int/float traps.

## 4. Math — add, subtract, multiply, divide, modulo

```
say(5 + 3)       # 8
say(10 - 4)      # 6
say(6 * 7)       # 42
say(10 / 4)      # 2.5   ← / is always true division (gives a float)
say(7 % 3)       # 1     ← the leftover (modulo)
say(2 + 3 * 4)   # 14    ← normal math precedence
say((2 + 3) * 4) # 20    ← brackets first
```

Plus the number tools: `abs(-5)` → `5`, `round(2.5)` → `3`,
`round(-2.5)` → `-3` (half away from zero — no surprises), `sqrt(9)` → `3.0`,
`random(1, 6)` → a dice roll, both ends included.

## 5. Text superpowers

```
"n = " + 5       # "n = 5"     ← text + anything = text
"ab" * 3         # "ababab"    ← repeat text
"hello"[1]       # "e"         ← index into text
"hello"[1:4]     # "ell"       ← slice text (see §12)
len("hello")     # 5
"apple" < "banana"   # true    ← text compares like a dictionary
```

## 6. Compare and logic

```
==  !=  <  <=  >  >=         # 3 > 2 → true
and   or   not               # the three logic words
in    not in                 # membership (see §13)
```

- `and` / `or` **short-circuit** — `false and 1/0 == 1` does NOT crash, the
  second part never runs. Safe!
- `true != 1` — bools and numbers are different worlds (clean categories)
- but `1 == 1.0` — true (same number family)

## 7. Decisions — `if` / `else if` / `else`

```
if x > 5 {
    say("big")
} else if x == 5 {
    say("equal")
} else {
    say("small")
}
```

## 8. Loops

### `while`
```
i = 0
while i < 3 {
    say(i)
    i = i + 1
}
# 0 1 2
```

### `for ... from ... to` — the range loop
```
for i from 1 to 5 { say(i) }    # 1 2 3 4 5   ← `to` is INCLUDED!
for i from 5 to 1 { say(i) }    # 5 4 3 2 1   ← start > end → counts down
```

### `for x in ...` — the walk-through loop
```
for x in [10, 20, 30] { say(x) }   # each item of a list
for ch in "ab" { say(ch) }         # each character of text
for k in {"a": 1} { say(k) }       # each KEY of a dict
```

### `break` / `continue` — the game buttons
```
for i from 1 to 10 {
    if i == 4 { break }         # stop the loop!
    if i % 2 == 0 { continue }  # skip to the next round
    say(i)
}
# 1 3
```
Both loop forms accept `break`/`continue`. Parse-time safety: `break`/`continue`
outside a loop is caught **before the program even starts**. A `for x in` loop
walks a **copy** of the list, so pushing items during the loop is safe.

## 9. `func` + `return`

```
func add(a, b) {
    return a + b
}
say(add(2, 3))    # 5

func hello() {
    say("hi")
}
hello()

func nothing() {
    return          # return nothing → null
}
```

- Recursion works (factorial, fibonacci) — too deep? friendly error.
- Parse-time safety: `return` outside a func is caught before running.
- Assignment inside a func is **local**; reading walks up to the globals.

## 10. Lists

```
fruits = ["apple", "mango", "grape"]
say(fruits[0])          # apple
fruits[2] = "apple"     # change an item
say(len(fruits))        # 3
say([1] + [2])          # [1, 2]     ← join lists
say(fruits)             # [apple, mango, apple]

grid = [[1, 2], [3, 4]] # 2D list (matrix)
grid[0][1] = 9
say(grid)               # [[1, 9], [3, 4]]
```

**Security:** every index is bounds-checked — `fruits[99]` never crashes
Python-style; it gives a human error:
`index 99 is out of range — this list has 3 items (0 to 2)`
The index must be a whole int; negative indexing (`a[-1]`) is not allowed.

## 11. Dicts — labelled boxes

```
person = {"name": "Aman", "age": 20}    # text keys
marks = {1: 90, 2: 85}                  # whole-number keys too
empty = {}                              # an empty dict

say(person["name"])     # Aman
say(person.name)        # Aman  ← dot sugar for READING only
person["age"] = 21      # add or change — always with ["key"] = value
say(len(person))        # 2
say("name" in person)   # true
say(person)             # {name: Aman, age: 21}   ← no quotes in display
```

The rules (they keep dicts simple and safe):

- keys are **text or whole numbers** — `d[1.5]`, `d[true]`, `d[[1]]` are errors:
  `a dict key must be text or a whole number — got: 1.5`
- reading a missing key is a friendly error, never `null` and never a crash:
  `key 'z' was not found — this dict has: a, b` (or `has 10 keys` if huge,
  or `this dict is empty`)
- `d.key = value` does not work — the error tells you to write
  `d["key"] = value` instead
- a dict is `false` when empty, `true` otherwise
- `d.name` is sugar for `d["name"]` — reading only

## 12. Slices — a piece of a list or text

```
say("abcdef"[2:])       # cdef
say("abcdef"[:3])       # abc
say("abcdef"[1:4])      # bcd
say([1, 2, 3, 4][1:3])  # [2, 3]
say([1, 2, 3][:])       # [1, 2, 3]   ← a whole copy
```

- slices **clamp, they never crash**: `[1, 2, 3][1:99]` → `[2, 3]`
- negative bounds are errors (`[-1:]`) — slices do not count backwards
- the bounds must be whole ints (`"ab"[0:1.5]` is an error)
- slices work on **lists and text** only

## 13. `in` and `not in` — is it there?

```
say(2 in [1, 2, 3])        # true
say("ell" in "hello")      # true
say("name" in {"a": 1})    # keys of a dict
say(4 not in [1, 2, 3])    # true
if "y" in word { say("yes") }
```

- on text, the left side must be text too: `5 in "abc"` is an error
- on dicts, `in` asks about **keys**
- membership uses the normal equality rules (`1 in [1.0]` → `true`,
  `true in [1]` → `false`)

## 14. Builtins — the 24-tool toolbox

The classics:
```
name = ask("your name: ")
age = int(ask("age: "))     # text → whole number
say(len(name))              # length of text, list, or dict
int("42")     # 42
int(2.9)      # 2
```

The Step 5 stdlib:
```
upper("juru")     # "JURU"    ← text only
lower("HELLO")    # "hello"   ← text only
str(42)           # "42"      ← anything → text (2.5 → "2.5", true → "true")
push(nums, 7)     # appends 7 IN PLACE and returns the list
sum([3, 1, 4])    # 8         ← numbers only; sum([]) is 0
min(3, 9)         # 3
max(3, 9)         # 9
```

```
nums = [1, 2]
push(nums, 3)
say(nums)         # [1, 2, 3]  ← the list itself changed
```

The Step 6 string + math tools:
```
split("a,b,c", ",")       # [a, b, c]      ← text → list
join([1, 2], "-")         # 1-2            ← list → text (readable display)
trim("  hi  ")            # hi             ← spaces/tabs/newlines off both ends
replace("aaa", "a", "b")  # bbb            ← every old → new
abs(-5)                   # 5
round(2.5)                # 3              ← half away from zero
round(-2.5)               # -3
random(1, 6)              # a whole number 1..6, both ends included
sqrt(9)                   # 3.0
```

The Step 9 list + dict tools (zero new keywords):
```
sorted([3, 1, 2])        # [1, 2, 3]  ← a NEW list; numbers OR text only
reverse([1, 2, 3])       # [3, 2, 1]  ← a NEW list; anything may ride along
find([5, 7, 9], 9)       # 2          ← first index; -1 when it is not there
find([1, 2], 99)         # -1
keys({"a": 1, "b": 2})   # [a, b]     ← the keys, in insertion order
values({"a": 1, "b": 2}) # [1, 2]     ← the values, in insertion order
count(["x", "y", "x"], "x")  # 2      ← how many times (same rules as ==)
```

Easy to remember: only `push` changes a list in place — `sorted` and
`reverse` hand you a fresh list and leave your original alone.

Guards that talk like a human:
- `split("a", "")` → `the split separator cannot be empty`
- `replace("a", "", "b")` → `the old text cannot be empty in replace()`
- `random(6, 1)` → `in random(low, high), low cannot be bigger than high (6 > 1)`
- `sqrt(-1)` → `sqrt(-1) — a negative number has no square root`
- `sorted(5)` → `sorted() needs a list — got: 5`
- `sorted([1, "a"])` → `sorted() needs a list of only numbers or only text — got: [1, a]`
- `keys([1])` → `keys() needs a dict — got: [1]`
- `count(5, 1)` → `count() needs a list first — got: 5`

All 24 are **reserved** — no variable or func can take their name, and both
the checker and the interpreter print the same argument-count message:
`push(list, item) takes exactly 2 arguments`.

## 15. Modules — code from another file

```
# helpers.jr
func double(n) {
    return n * 2
}
magic = 42
```

```
# main.jr
import "helpers.jr"        # the module gets the file's name: helpers
say(helpers.double(21))    # 42 — everything is namespaced: helpers.name
say(helpers.magic)         # 42
```

The rules:

- the module name is the **file name without `.jr`** — `lib/helpers.jr` →
  `helpers` (it must be a valid name: `my-utils.jr` is an error)
- a module runs **exactly once**, even if you import it ten times
- a module is **checked** first — a typo inside it never gets to run:
  `in 'helpers.jr': 'doubl' was not found`
- a module sees **nothing** from the file that imports it (isolation)
- import loops are caught: `import loop: a.jr -> b.jr -> a.jr — a file cannot
  import itself, even through other files`
- imports resolve next to **your file**, so `python3 juru.py src/main.jr`
  finds `src/helpers.jr`

## 16. Comments

```
# from # to the end of the line — the machine ignores it
```

## 17. Golden rules

1. One statement per line (no semicolons)
2. Blocks are `{ }` — no indentation headaches
3. A line may break after an operator (`x = 1 +` ↵ `2`) — and in the
   **REPL** a line that opens `{` / `(` / `[` keeps going on the `......> `
   prompt until the block closes; a bare `cancel` line drops an open block
4. New lines are allowed inside `( )` and `[ ]`
5. Text only in double quotes `"like this"`
6. No comparison chains (`1 < 2 < 3` is an error — use `and`)
7. Names: letters, digits, `_` (unicode letters work too — Devanagari incl.)
8. Dicts: write `d["key"] = value`, read with `d["key"]` or `d.key`

## 18. Errors that talk like a human

Every error says exactly where and what:
```
JuRu Error (line 3, col 10): missing closing " — text must be on one line
JuRu Error (line 5, col 9): index 7 is out of range — this list has 3 items (0 to 2)
JuRu Error (line 2, col 1): 'break' only works inside a loop (for / while)
JuRu Error (line 4, col 14): key 'z' was not found — this dict has: a, b
JuRu Error (line 1, col 1): import loop: a.jr -> b.jr -> a.jr — a file cannot import itself, even through other files
```

A typo gets the closest real name back (in the checker, at runtime, in dict
keys and module members alike):
```
JuRu Error (line 2, col 5): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
JuRu Error (line 1, col 5): key 'scorr' was not found — did you mean 'score'? — this dict has: score
JuRu Error (line 1, col 5): 'bolo' was not found (the old 'bolo' is now 'say')
```
A hopeless typo gets no guess at all — the message just stays plain.

Mistakes are caught in three layers — most of them BEFORE anything runs:

| When | Layer | Example it catches |
|------|-------|--------------------|
| before running (structure) | lexer + parser | missing `"`, missing `}`, `break` outside a loop |
| before running (meaning) | checker | typos: `'naame' was not found`, wrong argument counts, reserved names |
| while running | interpreter | index out of range, divide by zero, deep recursion, missing dict keys |

The checker is conservative — it only flags things that can definitely never
work, so it never complains about a program that would run fine.
Modules get the same treatment: their source is checked **before** they run.
Tip: `python3 checker.py file.jr` checks a file without running it.

## 19. Security by design 🛡️

- No `eval` — code is never built from strings
- `null` exists but the null-pointer bug class is blocked by design
- Every list index **bounds-checked** (no memory-safe escape hatches)
- **Runaway protection** — a loop over 10,000,000 steps stops itself
- Short-circuit logic — wrong order still never crashes
- Reserved builtins — the 24-tool toolbox can never be overwritten
- Dict keys are guarded; missing keys are errors, not `null`
- Modules are isolated and checked; import loops are detected
- Friendly type checks at runtime, with line/col on every error

## 20. The 19 keywords + 24 builtins

```
say  if  else  while  for  from  to  in
break  continue  func  return
true  false  null  and  or  not
import
```
```
ask( )   len( )    int( )     upper( )   lower( )   str( )
push( )  sum( )    min( )     max( )
split( ) join( )   trim( )    replace( )
abs( )   round( )  random( )  sqrt( )
sorted( )  reverse( )  find( )  keys( )  values( )  count( )
```
