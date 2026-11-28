# JuRu Syntax — The A to Z Cheat Sheet

> **File extension: `.jr`** (like `.py` for Python, `.c` for C — ours is `.jr`)
> **How to run:** `python3 juru.py program.jr`
> **Try it live:** `python3 repl.py`
> **Start from a template:** `python3 juru.py --new myprogram`
>
> The idea behind JuRu: code should feel like a **conversation in plain English**.
> Only 21 keywords — and they cover everything.

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
| set | `set_of([3, 1, 3])` → `{3, 1}` — no duplicates |
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
`random(1, 6)` → a dice roll, both ends included. `min` and `max` take one
or more numbers: `min(3, 9, 1)`, `max([7, 2, 4])`.

### Augmented assignment — the `+=` family
```
x = 5
x += 2     # 7      ← the shorthand for x = x + 2
x -= 3     # 4
x *= 2     # 8
x /= 4     # 2.0
x %= 3     # 2
x += "!"   # works on text too
nums[0] += 1        # one list item, in place
d["score"] += 10    # one dict value, in place
```

## 5. Text superpowers

```
"n = " + 5       # "n = 5"     ← text + anything = text
"ab" * 3         # "ababab"    ← repeat text
"hello"[1]       # "e"         ← index into text
"hello"[-1]      # "o"         ← -1 is the LAST character
"hello"[1:4]     # "ell"       ← slice text (see §12)
len("hello")     # 5
"apple" < "banana"   # true    ← text compares like a dictionary
```

More text tools:
```
index_of("hello", "ll")     # 2     ← where it starts, or -1
starts_with("hello", "he")  # true
ends_with("photo.png", ".png")  # true
ord("A")                    # 65    ← one character → its code number
chr(98)                     # "b"   ← a code number → its character
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
for x in set_of([2, 1]) { say(x) } # each value of a set, in order
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
say(fruits[-1])         # grape    ← -1 is the LAST item, -3 is the first
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
`index 99 is out of range — this list has 3 items (0 to 2)`.
Negative indexes count backwards: `-1` is the last item, and going past the
start is still a friendly error:
`index -4 is out of range — this list has 3 items (-3 to 2)`.
The index must be a whole int.

More list tools (insert/remove_at/clear/extend change the list IN place;
unique hands you a fresh list):
```
insert(nums, 0, 9)      # put 9 IN at position 0 — the rest shifts right
remove_at(nums, 0)      # take the item at 0 OUT and hand it back (-1 = last)
clear(nums)             # empty the list, in place
extend(nums, [3, 4])    # glue every item of the second list onto the end
unique([1, 2, 1, 3])    # [1, 2, 3]  ← a NEW list, first copy wins
```

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
- `d.name = value` does not work — the error tells you to write
  `d["key"] = value` instead
- a dict is `false` when empty, `true` otherwise
- `d.name` is sugar for `d["name"]` — reading only

Dict tools:
```
delete(prices, "cake")  # remove a key and its value, in place
items(prices)           # [[tea, 3], [cake, 5]]  ← the dict as [key, value] pairs
merge(a, b)             # a NEW dict: everything from a, then b (b wins)
```

## 12. Slices — a piece of a list or text

```
say("abcdef"[2:])       # cdef
say("abcdef"[:3])       # abc
say("abcdef"[1:4])      # bcd
say([1, 2, 3, 4][1:3])  # [2, 3]
say([1, 2, 3][:])       # [1, 2, 3]   ← a whole copy
say([1, 2, 3, 4, 5][::2])   # [1, 3, 5]   ← every 2nd item — the STEP
say([1, 2, 3, 4, 5][1:4:2]) # [2, 4]      ← start : end : step
say([1, 2, 3, 4, 5][::-1])  # [5, 4, 3, 2, 1]  ← step -1: back to front
say([1, 2, 3, 4, 5][-3:])   # [3, 4, 5]   ← negative bounds count backwards
```

- slices **clamp, they never crash**: `[1, 2, 3][1:99]` → `[2, 3]`
- negative bounds count backwards: `[-3:]` is the last three, `[:-2]` drops
  the last two — Python's rule, exactly
- the **step** must not be zero: `[::0]` → `the slice step cannot be zero`
- the bounds must be whole ints (`"ab"[0:1.5]` is an error)
- slices work on **lists and text** only

## 13. `in` and `not in` — is it there?

```
say(2 in [1, 2, 3])        # true
say("ell" in "hello")      # true
say("name" in {"a": 1})    # keys of a dict
say(2 in set_of([1, 2]))   # values of a set
say(4 not in [1, 2, 3])    # true
if "y" in word { say("yes") }
```

- on text, the left side must be text too: `5 in "abc"` is an error
- on dicts, `in` asks about **keys**
- membership uses the normal equality rules (`1 in [1.0]` → `true`,
  `true in [1]` → `false`)

## 14. Sets — a bag with no duplicates

A set is born from a list: `set_of([...])`. It keeps the FIRST-seen order
and drops the duplicates. `{ }` alone is still a dict — sets never have a
literal of their own.

```
s = set_of([3, 1, 3, 2])
say(s)          # {3, 1, 2}     ← no duplicates, first-seen order
say(len(s))     # 3
say(3 in s)     # true
say(s == set_of([2, 1, 3]))   # true  ← order does not matter
say(set_of([])) # set()         ← an empty set; it counts as false
say(sorted(s))  # [1, 2, 3]     ← a NEW sorted list
```

The set algebra (each hands back a NEW set):
```
a = set_of([1, 2, 3])
b = set_of([3, 4])
say(union(a, b))        # {1, 2, 3, 4}  ← everything from both
say(intersect(a, b))    # {3}           ← only what is in both
say(difference(a, b))   # {1, 2}        ← what is in a but not in b
```

Sets play by the ONE equality rule: `true != 1`, but `1 == 1.0`.
And like every collection, they refuse wrong tools in words:
`union([1], [2])` → `union() needs two sets — got: list and list
(build one with set_of([...]))`.

## 15. Builtins — the 67-tool toolbox

The classics:
```
name = ask("your name: ")
age = int(ask("age: "))     # text → whole number
say(len(name))              # length of text, list, dict, or set
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
min(3, 9)         # 3         ← one or more numbers, or a whole list: min(list)
max(3, 9)         # 9         ← max([7, 2, 4]) works too
```

```
nums = [1, 2]
push(nums, 3)
say(nums)         # [1, 2, 3]  ← the list itself changed
say(pop(nums))    # 3          ← takes the last item OUT (and hands it back)
say(nums)         # [1, 2]
```

`pop()` on an empty list is refused in words:
`pop() — this list is empty, there is nothing to take`.

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

The Step 12 input + math wave (zero new keywords):
```
float("3.5")    # 3.5        ← text → decimal (the other half of int())
float(5)        # 5.0        ← whole → decimal
pow(2, 10)      # 1024       ← exponents, no ** to memorize
pow(2, -2)      # 0.25
pow(9, 0.5)     # 3.0
type(5)         # int        ← one word: int, float, text, bool, null,
type("hi")      # text         list, dict, set, func, module
```

The collection wave (lists, dicts, text, sets — still zero new keywords):
```
insert(nums, 0, 9)          # put IN at a position, in place
remove_at(nums, 0)          # take OUT and hand back — -1 is the last
clear(nums)                 # empty the list, in place
extend(nums, [3, 4])        # glue a second list onto the end, in place
unique([1, 2, 1, 3])        # [1, 2, 3]  ← a NEW list without duplicates
delete(prices, "tea")       # remove a dict key, in place
items(prices)               # [[tea, 3]] ← the dict as [key, value] pairs
merge(a, b)                 # a NEW dict — b wins on shared keys
index_of("hello", "ll")     # 2          ← -1 when it is not there
starts_with("hi", "h")      # true
ends_with("a.png", ".png")  # true
ord("A")                    # 65         ← one character → its code
chr(98)                     # "b"        ← a code → its character
set_of([3, 1, 3])           # {3, 1}     ← a set: no duplicates, order kept
union(a_s, b_s)             # the set algebra — see §14
intersect(a_s, b_s)
difference(a_s, b_s)
```

The Batch-4 helpers (still zero new keywords):
```
help()          # the whole toolbox, one line per tool
help("pow")     # one card: what it does, worked examples, its guards
help("for")     # keyword cards work too; unknown names answer in words
sleep(1)        # pause one second — perfect between game rounds
```

Their guards:
- `help(5)` → `help() needs a name in quotes — got: 5`
- `help("a", "b")` → `help() takes at most 1 argument`
- `sleep(-1)` → `sleep() cannot go back in time — seconds cannot be negative (got: -1)`
- `sleep(31)` → `sleep() takes at most 30 seconds at a time (got: 31)`
- more than 120 s of sleep in one run → `sleep() — this program has slept more than 120 seconds in total; something may be stuck`

Guards that talk like a human (pow refuses impossible math BEFORE doing it):
- `float("abc")` → `float('abc') — 'abc' is not a number`
- `pow("2", 3)` → `pow() needs numbers — got: text and int`
- `pow(0, -1)` → `in pow(a, b), 0 cannot be raised to a negative power`
- `pow(-2, 0.5)` → `in pow(a, b), a negative base needs a whole-number exponent (got: 0.5)`
- `pow(2, 99999)` → `pow(2, 99999) — the result is too big to show`
- `pop(5)` → `pop() needs a list — got: 5`

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

Easy to remember: `push`, `pop`, `insert`, `remove_at`, `clear`, `extend`
and `delete` change the list/dict IN place — `sorted`, `reverse`, `unique`
and `merge` hand you a fresh one and leave your original alone.

Guards that talk like a human:
- `split("a", "")` → `the split separator cannot be empty`
- `replace("a", "", "b")` → `the old text cannot be empty in replace()`
- `random(6, 1)` → `in random(low, high), low cannot be bigger than high (6 > 1)`
- `sqrt(-1)` → `sqrt(-1) — a negative number has no square root`
- `sorted(5)` → `sorted() needs a list — got: 5`
- `sorted([1, "a"])` → `sorted() needs a list of only numbers or only text — got: [1, a]`
- `keys([1])` → `keys() needs a dict — got: [1]`
- `count(5, 1)` → `count() needs a list first — got: 5`

The files & JSON wave (Step 25 — still zero new keywords):
```
read_file("notes.txt")          # the whole file as text (UTF-8, 10 MB cap)
write_file("notes.txt", "hi")   # overwrite (folder must exist)
append_file("notes.txt", "!")   # add to the END, creating it if missing
read_lines("notes.txt")         # [hi!] — same rules as split_lines
write_lines("todo.txt", ["a", ""])  # writes "a\n\n" (final newline added)
file_exists("notes.txt")        # true — files AND folders
file_size("notes.txt")          # bytes (a folder is refused)
delete_file("notes.txt")        # one file — never a folder
list_dir(".")                   # sorted names inside a folder
make_dir("data/reports")        # creates parents too; existing folder = fine
delete_dir("empty")             # EMPTY folders only — never recursive
to_json({"a": [1, true]})       # {"a": [1, true]}
from_json("{\"a\": 1}")         # {a: 1}
```

Their guards:
- `read_file("missing.txt")` → `read_file() could not read 'missing.txt' — file not found (looked at: …)` (kind `"file"`)
- `write_file("x.txt", 5)` → `write_file() needs text to write — got: 5`
- `write_file("no/x.txt", "x")` → `… the folder does not exist`
- `write_lines("x.txt", ["a", 2])` → `… needs every line to be text — got: 2 at position 2`
- `delete_file("docs")` → `delete_file() refuses a folder — 'docs' is a folder; use delete_dir()`
- `delete_dir("data")` → `delete_dir() only removes an EMPTY folder — 'data' still has things in it`
- `to_json({1: "x"})` → `to_json() needs text keys in every dict — found 1 (JSON keys are always text)`
- `to_json(float("nan"))` → `to_json() cannot write a number that is not finite — JSON has no NaN or Infinity`

All 67 are **reserved** — no variable or func can take their name, and both
the checker and the interpreter print the same argument-count message:
`push(list, item) takes exactly 2 arguments`.

One builtin raises errors on purpose: `fail(message)` raises your own JuRu
error with kind `"fail"` — the nearest `try/rescue` catches it (section 18).

## 16. Formatting & alignment — `format`, padding, lines (Step 24, v1.11)

Build text without gluing `+` everywhere:

```
format("Name: {}, Age: {}", "Ravi", 20)   # Name: Ravi, Age: 20
format("x={0} y={1}", 10, 20)             # x=10 y=20
format("{0}-{0}-{1}", "ab", "cd")         # ab-ab-cd   ← repeats are fine
format("{{JuRu}} version {0}", "1.11")    # {JuRu} version 1.11
format("plain")                           # plain      ← no slots, no values
```

`{}` takes the next value left to right; `{0}`/`{1}` pick by index
(zero-based — `{007}` is slot 7); `{{` and `}}` are literal braces.
Values render exactly like `str()`/`say()` show them — `[1, 2]`,
`{a: 1}`, `true`, `null`. No code ever runs from the text: there is no
expression interpolation, no `eval` — `format()` formats values, nothing
else. The two slot styles never mix, and the count has to match:

- `format("{} {0}", 1)` → `format() cannot mix automatic {} slots and numbered {0} slots — pick one style for the whole text`
- `format("{}")` → `format() needs 1 more value — the text has more {} slots than values`
- `format("{2}", 1, 2)` → `format() slot {2} does not exist — only 2 values given (0 to 1)`
- `format("{0}", 1, 2)` → `format() got more values than slots — 2 values for 1 slot` (a typo should not vanish)
- `format("x{", 1)` → `format() found a lone '{' — write '{{' for a literal brace, or '{}' / '{0}' for a slot`
- `format("{x}", 1)` → `format() slot '{x}' is not a valid slot — a slot is '{}' or '{0}', '{1}', '{2}', …`

Numbered slots may skip — values fill positions `0` … highest index, so
`format("{0} and {2}", "a", "b", "c")` is fine and prints `a and c`.

Alignment — padding measures DISPLAY width (combining marks count 0,
East Asian wide characters count 2), never truncates, and leaves text
that is already wide enough untouched:

```
say("[" + pad_left("42", 5) + "]")     # [   42]
say("[" + pad_right("JuRu", 8) + "]")  # [JuRu    ]
say("[" + center("JuRu", 10) + "]")    # [   JuRu   ]
say("[" + center("hi", 5) + "]")       # [ hi  ]  ← an odd extra space goes right
say("[" + pad_left("は", 5) + "]")      # [   は]  ← wide char = 2 columns
```

- width must be a whole number (`pad_left("a", 2.5)` → `pad_left() needs a whole-number width — got: 2.5`)
- negative widths are refused (`pad_left() width cannot be negative — got: -1`)
- the budget is 10000 columns (`pad_right() width is too big — at most 10000 characters at a time`)

Lines — multiline text in, lines out; the list back into text:

```
say(split_lines("first\nsecond\nthird"))   # [first, second, third]
say(split_lines("a\n\nb"))                 # [a, , b]  ← blank lines are kept
say(split_lines(""))                       # []        ← an empty text has no lines
say(split_lines("a\n"))                    # [a]       ← a trailing newline opens no extra line
say(join_lines(["first", "second", "third"]))   # first ⏎ second ⏎ third
say("[" + join_lines([]) + "]")            # []        ← empty list → ""
```

`split_lines` splits on `\n`, `\r\n` and a lone `\r`; `join_lines` takes
text only (`join_lines() needs every line to be text — got: 2 at position 2`)
and preserves empty lines. They are partners:
`join_lines(split_lines(t))` gives `t` back whenever `t` does not end
with a newline. A small table the easy way:

```
rows = split_lines("name,age\nravi,20")
for row in rows {
    parts = split(row, ",")
    say(pad_right(parts[0], 6) + parts[1])
}
# name  age
# ravi  20
```

## 17. Files & JSON — real data, guarded (Step 25, v1.12)

Thirteen builtins read and write real files and speak JSON. They are
plain builtins — **zero new keywords** — and every mistake stays a
friendly, catchable JuRu error.

**Paths.** A relative path resolves against the folder of the running
program, exactly like `import`. Absolute paths are used as they are.
`~` is NOT expanded (it is a normal character), `..` is not refused
(this is an honest tool, guarded by sizes), NUL characters are refused,
and there are no glob patterns — `"*.txt"` is a literal name.

**Files** (UTF-8 text only; 10 MB per read/write/append/JSON text):

| Builtin | Hands back | Guards |
|---------|------------|--------|
| `read_file(path)` | the whole file as text | missing file, folder, bad UTF-8, permissions → kind `"file"` |
| `write_file(path, text)` | `null` | overwrites; the parent folder must exist; text ≤ 10 MB |
| `append_file(path, text)` | `null` | creates the file when missing; the RESULT ≤ 10 MB |
| `read_lines(path)` | list of lines | exactly `split_lines`'s rules (LF/CRLF/CR, no trailing empty line) |
| `write_lines(path, lines)` | `null` | list of ONE-line texts; adds the final newline; `[]` → empty file |
| `file_exists(path)` | `true` / `false` | never raises for a missing path |
| `file_size(path)` | whole number of BYTES | a folder or missing file is an error |
| `delete_file(path)` | `null` | always refuses a folder |
| `list_dir(path)` | sorted names | names only, never recursive; a file/missing folder is an error |
| `make_dir(path)` | `null` | creates parents; existing folder is a no-op; a file is refused |
| `delete_dir(path)` | `null` | EMPTY folders only — never recursive, so a typo cannot wipe a tree |

```
write_file("notes.txt", "first\n")
append_file("notes.txt", "second\n")
say(read_lines("notes.txt"))        # [first, second]
say(file_size("notes.txt"))         # 13  ← bytes, not characters

write_lines("todo.txt", ["milk", "", "bread"])
say(read_lines("todo.txt"))         # [milk, , bread]
say(write_lines("todo.txt", []) == null)   # true — [] writes an empty file

make_dir("data/reports")            # parents appear too
say(list_dir("."))                  # [data, notes.txt, todo.txt] (sorted)
delete_dir("data/reports")
delete_dir("data")
```

**JSON.** `to_json` writes text; `from_json` reads it back. Objects
become dicts with text keys, arrays become lists, and numbers keep
their `int`/`float` shape. Only `null`, booleans, finite numbers, text,
lists and dicts **with text keys** are JSON-able: funcs, modules, sets,
errors and integer keys are refused in words. Nesting is capped at 64
levels, every value that contains itself is refused, and NaN/Infinity
do not exist in JSON — both directions refuse them, as they do a JSON
number that overflows to Infinity. An unpaired surrogate escape (half
of a pair) is refused instead of producing text that cannot be shown.

```
data = {"name": "Ravi", "scores": [10, 20.5], "ok": true}
text = to_json(data)
say(text)                        # {"name": "Ravi", "scores": [10, 20.5], "ok": true}
back = from_json(text)
say(back["scores"][1])           # 20.5
say(type(back["scores"]))        # list

say(from_json("\"\\u0041\\u00e9\""))   # Aé — JSON escapes decode
say(from_json("{\"a\": 1, \"a\": 2}")["a"])   # 2 — the LAST duplicate wins
say(to_json(1.0))                # 1.0   ← Python-JSON float display
say(to_json(0.1 + 0.2))          # 0.30000000000000004
```

A bad file error is catchable like any other:
```
try {
    text = read_file("config.json")
} rescue as e {
    say(e.kind + ": " + e.message)     # file: read_file() could not read 'config.json' — file not found (looked at: …)
}
```

## 18. Errors you can catch — `try` / `rescue` (Step 23, v1.10)

Programs meet failure. Instead of dying, you can catch it:

```
try {
    text = ask("a number: ")
    n = int(text)
} rescue as e {
    say("could not read a number: " + e.message)
}
```

The `as e` is optional — plain `rescue { ... }` handles the error without
naming it. The rescue runs ONLY when the try raised a JuRu error; if
nothing went wrong, it never runs. Code after the try/rescue always runs.

**The caught error is a value with four parts:**

| field | what it holds |
|-------|---------------|
| `e.message` | the exact friendly error text you would have seen |
| `e.kind` | one short word — the category (see the table below) |
| `e.line` | the line where the error happened |
| `e.col` | the column where it happened |

**`e.kind` is always one of 11 fixed, documented words:**

| kind | raised when |
|------|-------------|
| `name` | a name was not found — variable, func, module member |
| `type` | a value had the wrong type for the operation (the default) |
| `value` | right type, bad value — empty, negative, unconvertible, out of range values |
| `arity` | wrong number of arguments |
| `math` | impossible arithmetic — divide by zero, `sqrt(-1)`, `pow` guards |
| `index` | list/text indexing or slicing went wrong |
| `key` | dict access went wrong — missing key, bad key |
| `loop` | a runaway loop or runaway recursion was stopped |
| `input` | `ask()` could not read an answer |
| `file` | a file or module could not be read |
| `fail` | raised by `fail()` — your own error |

Raise your own error with `fail(message)`:

```
try {
    if age < 0 {
        fail("age cannot be negative")
    }
    say("age ok")
} rescue as e {
    say(e.kind + ": " + e.message)     # fail: age cannot be negative
}
```

**Rules worth knowing:**
- only JuRu's own errors are catchable — internal bugs and loop signals
  (`break`, `continue`, `return`) pass straight through
- errors raised inside funcs reach the rescue that wraps the call
- a runtime error that crossed func calls remembers its JuRu call stack —
  shown as display-only `called from name (line n)` lines after the caret
  (top-level errors keep their exact old shape)
- the try's assignments survive a clean run; the rescue gets its own
  scope, so `e` (and rescue locals) never leak out
- there is no `finally`/`always` in JuRu — write cleanup after the block

## 19. Modules — code from another file

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

## 20. Comments

```
# from # to the end of the line — the machine ignores it
```

## 21. Golden rules

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

## 22. Errors that talk like a human

Every error says exactly where and what:
```
JuRu Error (line 3, col 10): missing closing " — text must be on one line
JuRu Error (line 5, col 9): index 7 is out of range — this list has 3 items (0 to 2)
JuRu Error (line 2, col 1): 'break' only works inside a loop (for / while)
JuRu Error (line 4, col 14): key 'z' was not found — this dict has: a, b
JuRu Error (line 1, col 1): import loop: a.jr -> b.jr -> a.jr — a file cannot import itself, even through other files
```

When the error crossed a func call, the display adds the JuRu call stack —
display-only `called from` lines after the caret (the message line itself
never changes, and top-level errors look exactly like they always did):
```
JuRu Error (line 2, col 11): cannot divide by zero (x / 0)
    say(1 / 0)
          ^
called from inner (line 5)
called from outer (line 7)
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

## 23. Security by design 🛡️

- No `eval` — code is never built from strings
- `null` exists but the null-pointer bug class is blocked by design
- Every list index **bounds-checked** (no memory-safe escape hatches)
- **Runaway protection** — a loop over 10,000,000 steps stops itself
- Short-circuit logic — wrong order still never crashes
- Reserved builtins — the 67-tool toolbox can never be overwritten
- File tools are capped (10 MB), never recursive, and refuse the wrong
  kind of path (`delete_dir` only empties an EMPTY folder)
- Dict keys are guarded; missing keys are errors, not `null`
- Modules are isolated and checked; import loops are detected
- Friendly type checks at runtime, with line/col on every error

## 24. The 21 keywords + 67 builtins

```
say  if  else  while  for  from  to  in
break  continue  func  return
true  false  null  and  or  not
import  try  rescue
```
```
ask( )   len( )    int( )     float( )   upper( )   lower( )   str( )
push( )  pop( )    sum( )     min( )     max( )
split( ) join( )   trim( )    replace( )
abs( )   round( )  random( )  sqrt( )
sorted( )  reverse( )  find( )  keys( )  values( )  count( )
pow( )  type( )  help( )  sleep( )
insert( )  remove_at( )  clear( )  extend( )  unique( )
delete( )  items( )  merge( )
index_of( )  starts_with( )  ends_with( )  ord( )  chr( )
set_of( )  union( )  intersect( )  difference( )  fail( )
format( )  pad_left( )  pad_right( )  center( )
split_lines( )  join_lines( )
read_file( )  write_file( )  append_file( )  read_lines( )  write_lines( )
file_exists( )  file_size( )  delete_file( )  list_dir( )
make_dir( )  delete_dir( )  to_json( )  from_json( )
```
