# Learn JuRu in one sitting

> **JuRu** is an easy, secure programming language: plain-English keywords,
> human error messages, zero setup. This tutorial takes you from zero to
> writing real programs — every code block below is executed by the test
> suite, so everything you see actually works.

One sitting, seventeen small chapters, one graduation project. Let's go.

## 1. The idea

Reading JuRu should feel like reading instructions:

```jr
name = "JuRu"
say("hello, " + name + "!")
```

```
hello, JuRu!
```

That is a complete program. Blocks live in `{ }`, comments start with `#`,
one statement per line — and that is most of the syntax you will ever need.

## 2. Start in one command

You never have to start from an empty file. Pick a template:

```bash
python3 juru.py --templates
```

Copy one into a fresh `.jr` file and run it:

```bash
python3 juru.py --new hello
python3 juru.py hello.jr
```

```text
created hello.jr from the 'starter' template
run it:  python3 juru.py hello.jr
hello, friend!
level 3, progress 7.5
step 1
step 2
step 3
you carry 4 items
[shield, potion]
```

The `--new` command never overwrites a file, and refuses names that would
be a nuisance (spaces, slashes, empty names). Chapter 14 shows every template.

## 3. Values and variables

A variable holds a value. You never declare a type — JuRu figures it out.
Print them and look:

```jr
age = 20               # a whole number
price = 19.99          # a decimal
name = "Aman"          # text, always in double quotes
happy = true           # true or false
nothing = null         # "no value yet"
say(age)
say(price)
say(name)
say(happy)
say(nothing)
```

```
20
19.99
Aman
true
null
```

Math works the way you expect — `/` is always real division:

```jr
say(10 + 4)
say(10 / 4)
say(10 % 4)
say(2 * 3.5)
```

```
14
2.5
2
7.0
```

## 4. Saying things

`say(...)` prints one line. Text joins anything with `+`:

```jr
say("JuRu means Jupyter + Ruby")
say("Level " + 3)
say("score: " + 97.5)
say(str(2.5) + " as text")
say("ab" * 3)
```

```
JuRu means Jupyter + Ruby
Level 3
score: 97.5
2.5 as text
ababab
```

## 5. Decisions

`if` / `else if` / `else` — two words, no `elif` keyword to memorize:

```jr
marks = 72
if marks >= 90 {
    say("grade A")
} else if marks >= 60 {
    say("grade B")
} else {
    say("work harder")
}
```

```
grade B
```

Conditions combine with `and`, `or`, `not`:

```jr
age = 15
has_pass = true
if age >= 18 or has_pass {
    say("come in")
}
if not (age >= 18) {
    say("still young")
}
```

```
come in
still young
```

JuRu's truthiness is simple: `null`, `0`, `""`, `[]` and `{}` are false,
everything else is true:

```jr
if 0 { say("no") } else { say("0 is false") }
if "" { say("no") } else { say("empty text is false") }
if [1] { say("a non-empty list is true") }
```

```
0 is false
empty text is false
a non-empty list is true
```

## 6. Loops

`for i from a to b` — the end value is included:

```jr
for i from 1 to 5 {
    say(i)
}
```

```
1
2
3
4
5
```

Start bigger than the end and it counts down:

```jr
for i from 3 to 1 {
    say(i)
}
```

```
3
2
1
```

`while` runs as long as the condition holds:

```jr
total = 0
i = 1
while i <= 10 {
    total = total + i
    i = i + 1
}
say(total)
```

```
55
```

`break` stops a loop, `continue` skips one round:

```jr
for i from 1 to 6 {
    if i == 3 {
        continue
    }
    if i == 6 {
        break
    }
    say(i)
}
```

```
1
2
4
5
```

`for x in things` walks any list (or text, dict keys, or set values):

```jr
for fruit in ["mango", "banana", "apple"] {
    say("I like " + fruit)
}
```

```
I like mango
I like banana
I like apple
```

## 7. Lists

```jr
nums = [3, 1, 4, 1, 5]
say(nums)
say(nums[0])
say(nums[2])
say(len(nums))
```

```
[3, 1, 4, 1, 5]
3
4
5
```

Replace one item, or add to the end:

```jr
nums = [3, 1, 4, 1, 5]
nums[1] = 99
say(nums)
push(nums, 7)
say(nums)
```

```
[3, 99, 4, 1, 5]
[3, 99, 4, 1, 5, 7]
```

Slices cut out a piece — the end is not included, and they never crash:

```jr
letters = ["a", "b", "c", "d", "e"]
say(letters[1:3])
say(letters[:2])
say(letters[3:])
```

```
[b, c]
[a, b]
[d, e]
```

The list toolbox:

```jr
say(sorted([3, 1, 2]))
say(reverse([1, 2, 3]))
say(find([5, 7, 9], 9))
say(count(["x", "y", "x"], "x"))
say(9 in [5, 7, 9])
```

```
[1, 2, 3]
[3, 2, 1]
2
2
true
```

`pop(list)` removes the last item **and** hands it back — the counterpart
of `push`. Together they make a stack:

```jr
stack = ["a", "b", "c"]
say(pop(stack))
say(stack)
push(stack, "z")
say(stack)
```

```
c
[a, b]
[a, b, z]
```

Two habits worth copying: only `push` and `pop` change a list in place —
`sorted` and `reverse` hand you a **new** list — and `find` answers `-1`
when the item is not there (never a crash):

```jr
nums = [3, 1, 2]
up = sorted(nums)
say(nums)
say(up)
say(find([5, 7, 9], 99))
```

```
[3, 1, 2]
[1, 2, 3]
-1
```

## 8. Dicts

A dict maps keys to values. Keys are text or whole numbers:

```jr
person = {"name": "Aman", "age": 20}
say(person)
say(person["name"])
say(person.age)
say(len(person))
```

```
{name: Aman, age: 20}
Aman
20
2
```

Add or change keys with `d["key"] = value`:

```jr
person = {"name": "Aman", "age": 20}
person["city"] = "Jaipur"
person["age"] = 21
say(person["city"])
say(person)
```

```
Jaipur
{name: Aman, age: 21, city: Jaipur}
```

`for key in dict` walks the keys, in insertion order:

```jr
person = {"name": "Aman", "age": 21, "city": "Jaipur"}
for key in person {
    say(key + " = " + str(person[key]))
}
```

```
name = Aman
age = 21
city = Jaipur
```

`keys()` and `values()` turn a dict into lists:

```jr
person = {"name": "Aman", "age": 21, "city": "Jaipur"}
say(keys({"a": 1, "b": 2}))
say(values({"a": 1, "b": 2}))
say("age" in person)
```

```
[a, b]
[1, 2]
true
```

A missing key is a friendly error, not a mystery:

```jr
person = {"name": "Aman"}
say(person["nope"])
```

```
JuRu Error (line 2, col 12): key 'nope' was not found — this dict has: name
```

## 9. Text, one character at a time

Text behaves like a list of characters — same indexing, same slices:

```jr
word = "hello"
say(word[0])
say(word[1:4])
say(len(word))
for ch in "ab" {
    say(ch)
}
```

```
h
ell
5
a
b
```

## 10. funcs

A func is a reusable piece with a name:

```jr
func add(a, b) {
    return a + b
}
say(add(2, 3))
say(add(10, -4))
```

```
5
6
```

funcs can print instead of return:

```jr
func greet(name) {
    say("hello, " + name + "!")
}
greet("JuRu")
greet("world")
```

```
hello, JuRu!
hello, world!
```

Recursion works — a func may call itself:

```jr
func factorial(n) {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}
say(factorial(5))
```

```
120
```

Scoping has one simple rule: **assignment inside a func is local**, reads
walk outward:

```jr
secret = "global"
func peek() {
    return secret
}
say(peek())
func hide() {
    secret = "local"
    return secret
}
say(hide())
say(secret)
```

```
global
local
global
```

## 11. The toolbox

All the tools live in one flat set of 54 builtins. Text tools:

```jr
say(upper("juru"))
say(lower("HELLO"))
say(trim("  hi  "))
say(replace("aaa", "a", "b"))
say(split("a,b,c", ","))
say(join([1, 2], "-"))
say(index_of("hello", "ll"))
say(starts_with("hello", "he"))
say(ends_with("photo.png", ".png"))
say(ord("A"))
say(chr(98))
```

```
JURU
hello
hi
bbb
[a, b, c]
1-2
2
true
true
65
b
```

`ord` and `chr` are a pair: `ord("A")` is `65`, `chr(65)` is `"A"`.

Formatting tools — build text without gluing `+` everywhere, and line it
up in columns:

```jr
say(format("Name: {}, Age: {}", "Ravi", 20))
say(format("x={0} y={1}", 10, 20))
say(format("{{JuRu}} version {0}", "1.11"))
say("[" + pad_left("42", 5) + "]")
say("[" + pad_right("JuRu", 8) + "]")
say("[" + center("JuRu", 10) + "]")
say(split_lines("first\nsecond\nthird"))
say(join_lines(["first", "second", "third"]))
```

```
Name: Ravi, Age: 20
x=10 y=20
{JuRu} version 1.11
[   42]
[JuRu    ]
[   JuRu   ]
[first, second, third]
first
second
third
```

`format` fills `{}` slots left to right, or `{0}`/`{1}` by index (repeat
them freely) — `{{` and `}}` are literal braces, and no code ever runs
from the text. The three padding tools measure DISPLAY width — wide
characters such as `は` count as 2 columns, combining accents as 0 — and
they never cut text off: text that is already wide enough comes back
unchanged. `split_lines` and `join_lines` are partners: one turns
multiline text into a list of lines, the other joins that list back
into text.

Math tools:

```jr
say(sum([3, 1, 4]))
say(abs(-5))
say(round(2.5))
say(round(-2.5))
say(sqrt(9))
say(pow(2, 10))
say(pow(9, 0.5))
say(int(2.9))
say(int("42"))
say(float("3.5"))
say(str(2.5))
say(min(3, 9))
say(max(3, 9))
say(min(5, 2, 8))
say(max([7, 2, 4]))
```

```
8
5
3
-3
3.0
1024
3.0
2
42
3.5
2.5
3
9
2
7
```

`pow(a, b)` raises to a power (no `**` to memorize) and refuses impossible
math in words — `pow(0, -1)` and `pow(-2, 0.5)` each get a one-line
explanation, never a crash. `float(x)` is the other half of `int(x)`: it
turns text (or a whole number) into a decimal. `min` and `max` take one
or more numbers — two, twenty, or a whole list.

List and dict tools:

```jr
nums = [3, 1, 2, 3]
insert(nums, 0, 9)          # [9, 3, 1, 2, 3]
say(remove_at(nums, 1))     # 3 — and nums is now [9, 1, 2, 3]
extend(nums, [7, 8])        # glue more onto the end, in place
say(unique(nums))           # [9, 1, 2, 3, 7, 8]
say(sorted(nums))           # [1, 2, 3, 7, 8, 9] — a NEW list
clear(nums)                 # nums is empty again: []
prices = {"tea": 3, "cake": 5}
delete(prices, "cake")      # remove a key, in place
say(items(prices))          # [[tea, 3]] — the dict as [key, value] pairs
say(merge({"a": 1}, {"a": 2, "b": 3}))   # b wins: {a: 2, b: 3}
```

```
3
[9, 1, 2, 3, 7, 8]
[1, 2, 3, 7, 8, 9]
[[tea, 3]]
{a: 2, b: 3}
```

Sets — a bag of values with no duplicates:

```jr
s = set_of([3, 1, 3, 2])
say(s)                      # {3, 1, 2} — first-seen order, dupes gone
say(len(s))
say(3 in s)
t = set_of([2, 4])
say(union(s, t))            # everything from both
say(intersect(s, t))        # only what is in both
say(difference(s, t))       # what is in s but not in t
```

```
{3, 1, 2}
3
true
{3, 1, 2, 4}
{2}
{3, 1}
```

A set shows as `{a, b, c}` (empty sets print `set()`), sorts with
`sorted(...)`, and walks with `for x in s`. `{ }` alone is still a dict —
sets are born from `set_of([...])`.

Membership works on text, lists, dicts and sets — and asks about **keys**
on dicts:

```jr
say("ell" in "hello")
say(7 in [1, 7, 9])
say("age" in {"age": 20})
say(2 in set_of([1, 2]))
say(5 not in [1, 2, 3])
```

```
true
true
true
true
true
```

## 12. Modules — code from another file

Put funcs in a `.jr` file, import it, use its names:

```jr
import "examples/test/helpers.jr"
say(helpers.double(21))
say(helpers.magic)
```

```
42
42
```

A module runs exactly once, is checked before it runs, and sees nothing
from the file that imports it.

## 13. When something goes wrong

Mistakes are normal — JuRu answers like a human, with the exact line and
column, and usually a hint:

```jr
name = "JuRu"
say(naame)
```

```
JuRu Error (line 2, col 5): 'naame' was not found — did you mean 'name'? (nothing with this name is ever assigned)
```

Out-of-range indexes are caught before they can hurt anything:

```jr
nums = [1, 2, 3]
say(nums[7])
```

```
JuRu Error (line 2, col 10): index 7 is out of range — this list has 3 items (0 to 2)
```

Math problems say what went wrong:

```jr
say(1 / 0)
```

```
JuRu Error (line 1, col 7): cannot divide by zero (x / 0)
```

```jr
say(sqrt(-1))
```

```
JuRu Error (line 1, col 9): sqrt(-1) — a negative number has no square root
```

### 13.1 Catching errors: try / rescue

Sometimes a failure is *expected* — text that may not be a number, a
key that may be missing. `try { ... }` runs risky code; the moment a
JuRu error happens, JuRu jumps to the `rescue` instead of stopping the
program. Write `rescue as e` to name the error, or plain `rescue` if
you do not need it:

```jr
try {
    n = int("not a number")
} rescue as e {
    say("caught: " + e.message)
}
say("still running")
```

```
caught: int('not a number') — 'not a number' is not a whole number
still running
```

A caught error is a value with four parts — `e.message` (the exact
friendly text), `e.kind` (a short category word), and the `e.line` /
`e.col` where it happened:

```jr
try {
    nums = [1, 2, 3]
    say(nums[99])
} rescue as e {
    say(e.kind + " at line " + e.line + ", col " + e.col)
    say(e.message)
}
```

```
index at line 3, col 14
index 99 is out of range — this list has 3 items (0 to 2)
```

`fail(message)` raises your own error — the nearest rescue catches it,
and its kind is `"fail"`:

```jr
try {
    fail("door stuck")
} rescue as e {
    say(e.kind + ": " + e.message)
}
```

```
fail: door stuck
```

An error outside any `try` is still the normal, loud, friendly error —
the rescue only protects its own `try`. There is no `finally` in JuRu:
if you always need a line to run, write it after the try/rescue.

And the 54 builtins can never be shadowed by accident:

```jr
count = 5
```

```
JuRu Error (line 1, col 1): 'count' is reserved (builtin) — pick another name
```

## 14. The templates gallery

Every template is a small, complete program — copy one and make it yours:

| Template | Start it with | What it teaches |
|----------|---------------|-----------------|
| `starter` | `python3 juru.py --new hello` | variables, loops, lists |
| `calculator` | `python3 juru.py --new calc calculator` | `while` + `split` + input |
| `quiz` | `python3 juru.py --new myquiz quiz` | lists + `ask` + scoring |
| `guessing_game` | `python3 juru.py --new game guessing_game` | `random` + hints |
| `word_stats` | `python3 juru.py --new stats word_stats` | `split` + `count` + `sorted` + `format` + `pad_right` |

## 15. Talking to your program: ask()

`ask(...)` reads one line from the user. It is the only tool that waits:

```jr
name = ask("your name: ")
say("nice to meet you, " + name + "!")
```

This block is interactive, so the test suite does not run it — but the
`quiz` and `calculator` templates use `ask` end to end, and their full
sessions are verified.

Whatever the user types arrives as **text**. `ask()` never converts for
you — you decide, with `int()`, `float()` and a guard first. The pattern
from the `calculator` template, in three steps:

```jr
age = ask("your age: ")        # text, even if they typed digits
if trim(age) == "" {
    say("please type something")
} else if type(age) == "text" and "." in age {
    say(float(age) + 1)        # "3.5" → 4.5
} else {
    say(int(age) + 1)          # "3" → 4
}
```

The same logic with a preset value, so you can see both branches pass:

```jr
raw = "3.5"
if trim(raw) == "" {
    say("empty")
} else if "." in raw {
    say(float(raw) * 2)
} else {
    say(int(raw) * 2)
}

raw = "7"
if trim(raw) == "" {
    say("empty")
} else if "." in raw {
    say(float(raw) * 2)
} else {
    say(int(raw) * 2)
}
```

```
7.0
14
```

If the user types something that is not a number, `int()` and `float()`
say exactly that — `float('abc') — 'abc' is not a number` — with the line
and column, and the program stops there. That is the honest behaviour:
never guess, never continue with a wrong value.

## 16. The REPL — try ideas instantly

Run `python3 repl.py` (or just `python3 juru.py` with no arguments — the
same REPL, exactly like typing `python`). Every entry runs against a
shared environment, so names survive from line to line. Blocks may span
lines — the `....>` prompt keeps going until the block closes, and a
bare `cancel` line drops an open block:

```text
$ python3 repl.py
JuRu 1.11 (easy like Python, secure like Rust) on linux
Type "help", "exit" or "cancel" for more information.
type help() to see the whole toolbox
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

Like Python, the REPL has a built-in helper: `help()` lists the whole
toolbox, and `help("pow")` prints one tool's card — what it does, worked
examples, and its guards. Games get `sleep(seconds)` to pause between
rounds: `sleep(1)` waits one second (at most 30 at a time, and a program
may sleep at most 120 seconds in total — runaway loops cannot hide).

One more Python-grade touch: the REPL knows what it is. Type a terminal
command at the prompt by mistake — `juru --version`, `pip`, `dir` — and
it does not answer with a scary "'juru' was not found" error. It answers
with one friendly line: this is the REPL, exit first, then run that
command in your terminal (and for `pip`: JuRu needs no pip, the whole
toolbox is already built in). Real JuRu code that uses those names —
`juru = 5`, `juru + 3` — still runs exactly as code.

## 17. Where to go next

Two folders full of runnable JuRu live under `examples/`, every output
verified by the test suite.

**The beginner guide** — `examples/guide/` teaches all 21 keywords in
15 small lessons, one keyword at a time. Start at `00_start_here.jr`
and read `examples/README.md` alongside it:

```text
00_start_here.jr  01_say.jr       02_if_else.jr     03_while.jr
04_counting.jr    05_for_in.jr    06_break.jr       07_continue.jr
08_func.jr        09_return.jr    10_booleans.jr    11_logic.jr
12_membership.jr  13_import.jr    14_try.jr         tools.jr
```

**The demo programs** — `examples/test/` holds fifteen complete
programs, every output verified by the test suite:

```text
demo.jr          patterns.jr      table.jr         funcs_demo.jr
lists_demo.jr    game_demo.jr     advanced_demo.jr number_lab.jr
algo_lab.jr      game_lab.jr      stdlib_demo.jr   mega_demo.jr
dicts_demo.jr    helpers.jr       import_demo.jr
```

Read `docs/syntax.md` when you want the whole language on one page, and
`design.md` when you want to know **why** it is built this way.

## 18. Graduation project

Everything from this tutorial in one small program — a word ranker:

```jr
text = "the cat saw the dog and the cat ran"
words = split(text, " ")
counts = {}
for w in words {
    counts[w] = count(words, w)
}
best = ""
top = 0
for w in keys(counts) {
    if counts[w] > top {
        top = counts[w]
        best = w
    }
}
say("total words: " + len(words))
say("unique words: " + len(keys(counts)))
say("winner: " + best + " (" + top + " times)")
say(sorted(words))
```

```
total words: 9
unique words: 6
winner: the (3 times)
[and, cat, cat, dog, ran, saw, the, the, the]
```

If you can read that program, you can write JuRu. Welcome aboard —
now go make something with `python3 juru.py --new myprogram`.
