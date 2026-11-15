"""JuRu help — the built-in documentation (Step 15).

`help()` in a program lists the whole toolbox; `help("pow")` prints one
topic's card: what it does, a worked example, and its guards. Everything
here is plain data — and a test suite (test_step15.py) checks that every
card is truthful: the examples must run, the guard lines must be the real
messages the language prints.
"""

# ---------------------------------------------------------------- overview
GROUPS = (
    ("output + input", (
        ("say(value)", "print one line"),
        ("ask(prompt)", "read one line the user types (always text)"),
        ("help(name)", "this help — call it with nothing, or with \"name\""),
        ("sleep(seconds)", "pause the program (games love this)"),
    )),
    ("text", (
        ("upper(x)", "text → CAPITALS"),
        ("lower(x)", "text → lowercase"),
        ("str(x)", "anything → text"),
        ("trim(x)", "drop spaces/tabs/newlines from both ends"),
        ("replace(text, old, new)", "swap every old for new"),
        ("split(text, sep)", "text → list of pieces"),
        ("join(list, sep)", "list → text"),
    )),
    ("numbers", (
        ("int(x)", "text/float → whole number"),
        ("float(x)", "text/int → decimal"),
        ("abs(x)", "distance from zero"),
        ("round(x)", "nearest whole number, half away from zero"),
        ("min(a, b)", "the smaller number"),
        ("max(a, b)", "the bigger number"),
        ("sum(list)", "add every number (empty → 0)"),
        ("sqrt(x)", "square root"),
        ("pow(a, b)", "a to the power b — the exponent tool"),
        ("random(low, high)", "one whole number, both ends included"),
    )),
    ("lists + dicts", (
        ("len(x)", "how many items (text, list or dict)"),
        ("push(list, item)", "add to the end, in place"),
        ("pop(list)", "take the last item out and hand it back"),
        ("sorted(list)", "a NEW sorted list (numbers or text)"),
        ("reverse(list)", "a NEW reversed list"),
        ("find(list, item)", "first index of item, or -1"),
        ("count(list, item)", "how many times item appears"),
        ("keys(dict)", "the keys as a list, in order"),
        ("values(dict)", "the values as a list, in order"),
        ("type(x)", "one word: int, float, text, bool, null, list, dict, func, module"),
    )),
)

KEYWORD_LINES = (
    ("say value", "print a line"),
    ("if / else if / else", "decisions — blocks in { }"),    ("while cond", "repeat while the condition is true"),
    ("for i from a to b", "count — the end value b is included"),
    ("for x in things", "walk a list, text or dict"),
    ("break / continue", "stop a loop / skip one round"),
    ("func name(args)", "a reusable piece with a name"),
    ("return value", "hand a value back from a func"),
    ("true / false / null", "yes / no / nothing yet"),
    ("and / or / not", "combine conditions"),
    ("x in list", "membership — also x not in list, and keys in dicts"),
    ("import \"file.jr\"", "code from another file"),
)

USAGE_LINE = 'call help("name") with any keyword or builtin to see its card.'


def overview():
    parts = ["JuRu toolbox — {} keywords + {} builtins, all in one flat set.\n"
             .format(len(KEYWORD_CARDS), len(BUILTIN_CARDS))]
    for title, entries in GROUPS:
        parts.append(title + ":")
        width = max(len(name) for name, _ in entries)
        for name, line in entries:
            parts.append("  {}  {}".format(name.ljust(width), line))
        parts.append("")
    parts.append("keywords:")
    width = max(len(name) for name, _ in KEYWORD_LINES)
    for name, line in KEYWORD_LINES:
        parts.append("  {}  {}".format(name.ljust(width), line))
    parts.append("")
    parts.append(USAGE_LINE)
    return "\n".join(parts)


# ---------------------------------------------------------------- cards
BUILTIN_CARDS = {
    "ask": ("ask(prompt)",
            "read one line of typed input. The answer is ALWAYS text —\n"
            "convert it yourself with int() or float().",
            ['name = ask("your name: ")',
             'age = int(ask("your age: "))      # digits → whole number',
             'height = float(ask("height: "))   # decimals work too'],
            ["ask(prompt) takes at most 1 argument",
             "if the input ends before an answer arrives, ask() explains "
             "itself instead of crashing"]),
    "sleep": ("sleep(seconds)",
              "pause the program for a moment — perfect between game rounds.",
              ['say("ready?")',
               "sleep(1)",
               'say("go!")'],
              ["sleep(seconds) takes exactly 1 argument",
               "sleep() needs a number of seconds",
               "sleep() cannot go back in time — seconds cannot be negative",
               "sleep() takes at most 30 seconds at a time",
               "a program may sleep at most 120 seconds in total"]),
    "len": ("len(x)",
            "how many characters in text, items in a list, keys in a dict.",
            ['len("hello")   # 5',
             "len([1, 2, 3]) # 3",
             'len({"a": 1})  # 1'],
            ["len(x) takes exactly 1 argument"]),
    "int": ("int(x)",
            "turn text or a decimal into a whole number. Decimals are cut\n"
            "toward zero (int(2.9) is 2, int(-2.9) is -2).",
            ['int("42")   # 42',
             "int(2.9)    # 2",
             'int("  7 ") # 7  (spaces are trimmed)'],
            ["int(x) — this cannot be converted to int",
             "int('3.7') — '3.7' is not a whole number"]),
    "float": ("float(x)",
              "turn text or a whole number into a decimal — the other half of int().",
              ['float("3.5") # 3.5',
               "float(5)     # 5.0",
               'float("-2")  # -2.0'],
              ["float(x) — this cannot be converted to float",
               "float('abc') — 'abc' is not a number"]),
    "upper": ("upper(x)",
              "text → CAPITALS. Text only.",
              ['upper("juru") # JURU'],
              ["upper(x) takes exactly 1 argument",
               "upper() needs text — got: 5"]),
    "lower": ("lower(x)",
              "text → lowercase. Perfect before comparing answers.",
              ['lower("HELLO") # hello',
               'lower(ask("answer: ")) == "paris"  # forgiving comparison'],
              ["lower(x) takes exactly 1 argument",
               "lower() needs text"]),
    "str": ("str(x)",
            "anything → text, so it can join other text with +.",
            ['str(2.5)     # 2.5',
             'str(true)    # true',
             '"score: " + str(97.5)  # score: 97.5'],
            ["str(x) takes exactly 1 argument"]),
    "trim": ("trim(x)",
             "drop spaces, tabs and newlines from both ends — great on ask() answers.",
             ['trim("  hi  ")      # hi',
              'trim(ask("name: ")) == ""  # did they type nothing?'],
             ["trim(x) takes exactly 1 argument",
              "trim() needs text"]),
    "replace": ("replace(text, old, new)",
                "swap every old for new, in a NEW text.",
                ['replace("aaa", "a", "b")  # bbb',
                 'replace("2026-11-14", "-", "/")  # 2026/11/14'],
                ["replace(text, old, new) takes exactly 3 arguments",
                 "the old text cannot be empty in replace()"]),
    "split": ("split(text, sep)",
              "cut text into a list at every sep.",
              ['split("a,b,c", ",")  # [a, b, c]',
               'split("one two three", " ")  # [one, two, three]'],
              ["split(text, separator) takes exactly 2 arguments",
               "the split separator cannot be empty"]),
    "join": ("join(list, sep)",
             "glue a list back into one text, sep between pieces.",
             ['join([1, 2, 3], "-")  # 1-2-3',
              'join(["a", "b"], "")  # ab  (empty glue is allowed here)'],
             ["join(list, separator) takes exactly 2 arguments",
              "join() needs a list"]),
    "push": ("push(list, item)",
             "add item to the END of the list, in place. Returns the list.",
             ["nums = [1, 2]",
              "push(nums, 3)",
              "say(nums)             # [1, 2, 3]"],
             ["push(list, item) takes exactly 2 arguments",
              "push() needs a list — got: 5"]),
    "pop": ("pop(list)",
            "take the LAST item out of the list and hand it back.\n"
            "The counterpart of push — together they make a stack.",
            ["stack = [\"a\", \"b\", \"c\"]",
             "say(pop(stack))  # c  (and the list is now [a, b])",
             "say(pop(stack))  # b"],
            ["pop(list) takes exactly 1 argument",
             "pop() needs a list — got: 5",
             "pop() — this list is empty, there is nothing to take"]),
    "sum": ("sum(list)",
            "add every number in a list. An empty list adds up to 0.",
            ["sum([3, 1, 4]) # 8",
             "sum([])        # 0"],
            ["sum(list) takes exactly 1 argument",
             "sum() needs a list",
             "sum() needs only numbers — found: a"]),
    "min": ("min(a, b)", "the smaller of two numbers.",
            ["min(3, 9) # 3", "min(-2, -5) # -5"],
            ["min(a, b) takes exactly 2 arguments",
             "min() needs numbers"]),
    "max": ("max(a, b)", "the bigger of two numbers.",
            ["max(3, 9) # 9", "max(1.5, 1) # 1.5"],
            ["max(a, b) takes exactly 2 arguments",
             "max() needs numbers"]),
    "abs": ("abs(x)", "distance from zero — negatives become positive.",
            ["abs(-5) # 5", "abs(5) # 5", "abs(-2.5) # 2.5"],
            ["abs(x) takes exactly 1 argument",
             "abs() needs a number"]),
    "round": ("round(x)",
              "nearest whole number, halves go AWAY from zero (2.5 → 3, -2.5 → -3).",
              ["round(2.5)  # 3",
               "round(-2.5) # -3",
               "round(2.4)  # 2"],
              ["round(x) takes exactly 1 argument",
               "round() needs a number"]),
    "random": ("random(low, high)",
               "one whole number between low and high — BOTH ends included.",
               ["random(1, 6)      # a dice roll: 1..6",
                "secret = random(1, 100)  # the guessing-game trick"],
               ["random(low, high) takes exactly 2 arguments",
                "in random(low, high), low cannot be bigger than high (6 > 1)",
                "random() needs whole numbers"]),
    "sqrt": ("sqrt(x)", "square root.",
             ["sqrt(9) # 3.0", "sqrt(2) # 1.4142135623730951"],
             ["sqrt(x) takes exactly 1 argument",
              "sqrt(-1) — a negative number has no square root"]),
    "pow": ("pow(a, b)",
            "raise a to the power b — the exponent tool (no ** to memorize).\n"
            "Impossible math is refused in words, never silently wrong.",
            ["pow(2, 10)  # 1024",
             "pow(2, -2)  # 0.25",
             "pow(9, 0.5) # 3.0  (the square root, another way)"],
            ["pow(a, b) takes exactly 2 arguments",
             "pow() needs numbers — got: text and int",
             "in pow(a, b), 0 cannot be raised to a negative power",
             "in pow(a, b), a negative base needs a whole-number exponent (got: 0.5)",
             "the result is too big to show"]),
    "sorted": ("sorted(list)",
               "a NEW list, sorted small→big. Numbers only, or text only.\n"
               "Your original list is never touched.",
               ["sorted([3, 1, 2])   # [1, 2, 3]",
                'sorted(["b", "a"])  # [a, b]'],
               ["sorted(list) takes exactly 1 argument",
                "sorted() needs a list — got: 5",
                "sorted() needs a list of only numbers or only text — got: [1, a]"]),
    "reverse": ("reverse(list)",
                "a NEW list, back to front. Anything may ride along.",
                ["reverse([1, 2, 3])  # [3, 2, 1]",
                 'reverse(["a", "b"]) # [b, a]'],
                ["reverse(list) takes exactly 1 argument",
                 "reverse() needs a list"]),
    "find": ("find(list, item)",
             "the first index of item, or -1 when it is not there — never a crash.",
             ["find([5, 7, 9], 9)  # 2",
              "find([5, 7, 9], 99) # -1"],
             ["find(list, item) takes exactly 2 arguments",
              "find() needs a list"]),
    "count": ("count(list, item)",
              "how many times item appears, with the same equality as ==.",
              ['count(["x", "y", "x"], "x")  # 2',
               "count([[1], [1]], [1])      # 2  (lists count too)"],
              ["count(list, item) takes exactly 2 arguments",
               "count() needs a list first — got: 5"]),
    "keys": ("keys(dict)",
             "the dict's keys as a list, in the order you added them.",
             ['keys({"a": 1, "b": 2})  # [a, b]',
              "for key in keys(d) { ... }  # or just: for key in d { ... }"],
             ["keys(dict) takes exactly 1 argument",
              "keys() needs a dict — got: [1]"]),
    "values": ("values(dict)",
               "the dict's values as a list, in key order.",
               ['values({"a": 1, "b": 2})  # [1, 2]'],
               ["values(dict) takes exactly 1 argument",
                "values() needs a dict"]),
    "type": ("type(x)",
             "one word for what x is: int, float, text, bool, null, list,\n"
             "dict, func or module. Never fails, never crashes.",
             ['type(5)      # int',
              'type("hi")   # text',
              'type([1])    # list',
              'if type(answer) == "text" { say("please type a number") }'],
             ["type(x) takes exactly 1 argument"]),
    "help": ("help(name)",
             "print how to use any keyword or builtin. Call it with nothing\n"
             "to see the whole toolbox at once.",
             ["help()          # the whole toolbox, one line each",
              'help("pow")     # this card',
              'help("for")     # keyword cards too',
              "say(help(\"type\")) is the same as help(\"type\") — it prints"],
             ["help() takes at most 1 argument",
              "help() needs a name in quotes — got: 5",
              "an unknown name gets did-you-mean and the topic list"]),
}

KEYWORD_CARDS = {
    "say": ("say value",
            "print one line. Text joins anything with +.",
            ['say("hello, " + "world")  # hello, world',
             'say("level " + 3)          # level 3',
             'say(2 + 2)                 # 4'],
            ["one say = one line; str() it first if you like it tidy"]),
    "if": ("if cond { ... } else if cond { ... } else { ... }",
           "decide. Blocks live in { } — `else if` is two words, no elif.",
           ["marks = 72",
            "if marks >= 90 {",
            "    say(\"grade A\")",
            "} else if marks >= 60 {",
            "    say(\"grade B\")",
            "} else {",
            "    say(\"work harder\")",
            "}"],
           ["conditions combine with and / or / not",
            "false values: null, 0, empty text, empty list, empty dict"]),
    "else": ("} else { ... }   or   } else if cond { ... }",
             "the other branch of an if. `else if` is two words — no elif.",
             ["if marks > 90 {",
              "    say(\"great\")",
              "} else if marks > 60 {",
              "    say(\"good\")",
              "} else {",
              "    say(\"try again\")",
              "}"],
             ["else always pairs with an if just above it"]),
    "while": ("while cond { ... }",
              "repeat while the condition holds. break stops, continue skips.",
              ["i = 1",
               "while i <= 3 {",
               "    say(i)",
               "    i = i + 1",
               "}"],
              ["while true { ... } needs a break — runaway loops stop "
               "themselves at 10,000,000 steps"]),
    "for": ("for i from a to b { ... }   or   for x in things { ... }",
            "count from a to b (the end b is INCLUDED), or walk a list, "
            "text or dict.",
            ["for i from 1 to 3 { say(i) }      # 1, 2, 3",
             'for ch in "ab" { say(ch) }        # a, b',
             "for key in {\"a\": 1} { say(key) }  # a  (walks the keys)"],
            ["counting down works too: from 3 to 1",
            "the loop variable is fresh each round"]),
    "from": ("for i from a to b",
             "the starting number of a counting loop (used with to).",
             ["for i from 5 to 7 { say(i) }  # 5, 6, 7"],
             []),
    "to": ("for i from a to b",
           "the ending number of a counting loop — it IS included.",
           ["for i from 1 to 3 { say(i) }  # 1, 2, 3 (three rounds!)"],
           []),
    "in": ("x in things     or     x not in things",
           "membership: text inside text, item inside list, key inside dict.",
           ['"ell" in "hello"    # true',
            "7 in [1, 7, 9]      # true",
            '"age" in person     # asks about KEYS in dicts',
            "5 not in [1, 2, 3]  # true"],
           []),
    "break": ("break",
              "stop the loop you are inside, right now.",
              ["while true {",
              "    break   # otherwise this would never end",
              "}"],
              ["break only works inside a loop (for / while)"]),
    "continue": ("continue",
                 "skip the rest of this round, go to the next one.",
                 ["for i from 1 to 4 {",
                  "    if i == 2 { continue }",
                  "    say(i)   # 1, 3, 4 — the 2 is skipped",
                  "}"],
                 ["continue only works inside a loop"]),
    "func": ("func name(a, b) { ... }",
             "a reusable piece with a name. Assignment inside is local.",
             ["func add(a, b) {",
              "    return a + b",
              "}",
              "say(add(2, 3))  # 5"],
             ["duplicate parameters are rejected: func f(a, a)",
             "builtins can never be shadowed by a func"]),
    "return": ("return value",
               "hand a value back and leave the func at once.",
               ["func double(n) {",
                "    return n * 2",
                "}",
                "say(double(21))  # 42"],
               ["a func with no return hands back null"]),
    "true": ("true", "yes — one of two booleans.",
             ['say(3 > 2)        # true',
              'if true { say("runs") }'],
             []),
    "false": ("false", "no — the other boolean.",
              ['say(2 > 3)       # false',
               'if not false { say("runs") }'],
              []),
    "null": ("null", "\"no value yet\" — the empty seat.",
             ['name = null',
              'say(name)         # null',
              'say(name == null) # true'],
             ["indexing through null is a friendly error, not a crash"]),
    "and": ("a and b", "both sides must be true.",
            ["if age >= 13 and has_pass { say(\"come in\") }",
             "say(true and false)  # false"],
            ["short-circuit: if the left side is false, the right side "
             "never runs"]),
    "or": ("a or b", "at least one side must be true.",
           ["if day == \"sat\" or day == \"sun\" { say(\"weekend!\") }",
            "say(true or false)  # true"],
           ["short-circuit: if the left side is true, the right side "
            "never runs"]),
    "not": ("not cond", "flip true ↔ false.",
            ["if not (age >= 18) { say(\"still young\") }",
             "say(not true)  # false"],
            []),
    "import": ("import \"file.jr\"",
               "run another JuRu file and use its names through the module.\n"
               "helpers.jr becomes `helpers`.",
               ["import \"examples/helpers.jr\"",
                "say(helpers.double(21))  # 42",
                "say(helpers.magic)       # 42"],
               ["modules run exactly once, are checked before running,",
                "and see nothing from the file that imports them"]),
}

# names people might type — help should find them anyway
ALIASES = {
    "print": "say",
    "input": "ask",
    "output": "say",
    "wait": "sleep",
    "pause": "sleep",
    "power": "pow",
    "exponent": "pow",
    "length": "len",
    "size": "len",
    "sort": "sorted",
    "del": "pop",
    "remove": "pop",
    "last": "pop",
    "square root": "sqrt",
}


def _cards_for(kind):
    return BUILTIN_CARDS if kind == "builtin" else KEYWORD_CARDS


def topics():
    """(name, kind) for every card — builtins first, then keywords."""
    all_topics = [(n, "builtin") for n in BUILTIN_CARDS]
    all_topics += [(n, "keyword") for n in KEYWORD_CARDS]
    return all_topics


def topic_names():
    return sorted(n for n, _ in topics())


def card_for(name):
    """The card text for name (alias-aware), or None when unknown."""
    low = name.strip().lower()
    low = ALIASES.get(low, low)
    if low in BUILTIN_CARDS:
        return _render(BUILTIN_CARDS[low], "builtin")
    if low in KEYWORD_CARDS:
        return _render(KEYWORD_CARDS[low], "keyword")
    return None


def _render(card, kind):
    signature, what, examples, guards = card
    parts = [signature, "", what, ""]
    if examples:
        for line in examples:
            parts.append("  " + line)
        parts.append("")
    if guards:
        parts.append("guards:")
        for line in guards:
            parts.append("  - " + line)
        parts.append("")
    parts.append("({})".format(kind))
    return "\n".join(parts)


def unknown(name):
    """The friendly answer for an unknown help topic."""
    from .checker import did_you_mean
    close = did_you_mean(name, topic_names())
    head = "no help topic '{}'".format(name)
    if close:
        head += " — did you mean '{}'?".format(close)
    head += "\nthe topics are: " + ", ".join(topic_names())
    return head
