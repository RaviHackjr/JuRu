"""JuRu stdlib — the builtin registry (the single source of truth).

Every reserved builtin lives here ONCE: its name, its argument rules,
and the exact message shown when the count is wrong. The checker reads
this table before a program runs; the interpreter reads the same table
at runtime — so both layers can never drift apart again.

    checker:  wrong count → refuse, before a single line runs
    runtime:  wrong count → the same message, at the call's line/col

The handlers themselves stay in the interpreter (they need its eval,
its equality rules, its display) — this file is pure data, so nothing
here can create import loops.
"""

# The reserved builtin names, in the order they arrived in JuRu.
# Reserved means: never shadowable, not by assignment, not by func,
# not even as an imported module's name.
BUILTINS = ("ask", "len", "int", "float", "upper", "lower", "str", "push", "pop",
            "sum", "min", "max",
            "split", "join", "trim", "replace", "abs", "round", "random", "sqrt",
            "sorted", "reverse", "find", "keys", "values", "count",
            "pow", "type", "help", "sleep",
            # Step 22 — collections & ergonomics: lists, dicts, text, sets
            "insert", "remove_at", "clear", "extend", "unique",
            "delete", "items", "merge",
            "index_of", "starts_with", "ends_with", "ord", "chr",
            "set_of", "union", "intersect", "difference",
            # Step 23 — errors you can catch: try / rescue + fail
            "fail",
            # Step 24 — text & formatting wave
            "format", "pad_left", "pad_right", "center",
            "split_lines", "join_lines",
            # Step 25 — files & JSON wave
            "read_file", "write_file", "append_file", "read_lines", "write_lines",
            "file_exists", "file_size", "delete_file", "list_dir",
            "make_dir", "delete_dir", "to_json", "from_json")

# (min_args, max_args) for every builtin — checked before a single line
# runs. max None = "one or more" (a variadic builtin, like min/max).
BUILTIN_ARITY = {
    "ask": (0, 1),
    "len": (1, 1),
    "int": (1, 1),
    "float": (1, 1),
    "upper": (1, 1),
    "lower": (1, 1),
    "str": (1, 1),
    "push": (2, 2),
    "pop": (1, 1),
    "sum": (1, 1),
    "min": (1, None),
    "max": (1, None),
    "split": (2, 2),
    "join": (2, 2),
    "trim": (1, 1),
    "replace": (3, 3),
    "abs": (1, 1),
    "round": (1, 1),
    "random": (2, 2),
    "sqrt": (1, 1),
    "sorted": (1, 1),
    "reverse": (1, 1),
    "find": (2, 2),
    "keys": (1, 1),
    "values": (1, 1),
    "count": (2, 2),
    "pow": (2, 2),
    "type": (1, 1),
    "help": (0, 1),
    "sleep": (1, 1),
    "insert": (3, 3),
    "remove_at": (2, 2),
    "clear": (1, 1),
    "extend": (2, 2),
    "unique": (1, 1),
    "delete": (2, 2),
    "items": (1, 1),
    "merge": (2, 2),
    "index_of": (2, 2),
    "starts_with": (2, 2),
    "ends_with": (2, 2),
    "ord": (1, 1),
    "chr": (1, 1),
    "set_of": (1, 1),
    "union": (2, 2),
    "intersect": (2, 2),
    "difference": (2, 2),
    "fail": (1, 1),
    "format": (1, None),
    "pad_left": (2, 2),
    "pad_right": (2, 2),
    "center": (2, 2),
    "split_lines": (1, 1),
    "join_lines": (1, 1),
    "read_file": (1, 1),
    "write_file": (2, 2),
    "append_file": (2, 2),
    "read_lines": (1, 1),
    "write_lines": (2, 2),
    "file_exists": (1, 1),
    "file_size": (1, 1),
    "delete_file": (1, 1),
    "list_dir": (1, 1),
    "make_dir": (1, 1),
    "delete_dir": (1, 1),
    "to_json": (1, 1),
    "from_json": (1, 1),
}

# The exact message both layers print for a wrong argument count —
# one human sentence, in the same style as every JuRu error.
BUILTIN_HINT = {
    "ask": "ask(prompt) takes at most 1 argument",
    "len": "len(x) takes exactly 1 argument",
    "int": "int(x) takes exactly 1 argument",
    "float": "float(x) takes exactly 1 argument",
    "upper": "upper(x) takes exactly 1 argument",
    "lower": "lower(x) takes exactly 1 argument",
    "str": "str(x) takes exactly 1 argument",
    "push": "push(list, item) takes exactly 2 arguments",
    "pop": "pop(list) takes exactly 1 argument",
    "sum": "sum(list) takes exactly 1 argument",
    "min": "min() takes one or more arguments — like min(a, b) or min(list)",
    "max": "max() takes one or more arguments — like max(a, b) or max(list)",
    "split": "split(text, separator) takes exactly 2 arguments",
    "join": "join(list, separator) takes exactly 2 arguments",
    "trim": "trim(x) takes exactly 1 argument",
    "replace": "replace(text, old, new) takes exactly 3 arguments",
    "abs": "abs(x) takes exactly 1 argument",
    "round": "round(x) takes exactly 1 argument",
    "random": "random(low, high) takes exactly 2 arguments",
    "sqrt": "sqrt(x) takes exactly 1 argument",
    "sorted": "sorted(list) takes exactly 1 argument",
    "reverse": "reverse(list) takes exactly 1 argument",
    "find": "find(list, item) takes exactly 2 arguments",
    "keys": "keys(dict) takes exactly 1 argument",
    "values": "values(dict) takes exactly 1 argument",
    "count": "count(list, item) takes exactly 2 arguments",
    "pow": "pow(a, b) takes exactly 2 arguments",
    "type": "type(x) takes exactly 1 argument",
    "help": "help() takes at most 1 argument",
    "sleep": "sleep(seconds) takes exactly 1 argument",
    "insert": "insert(list, i, item) takes exactly 3 arguments",
    "remove_at": "remove_at(list, i) takes exactly 2 arguments",
    "clear": "clear(list) takes exactly 1 argument",
    "extend": "extend(list, more) takes exactly 2 arguments",
    "unique": "unique(list) takes exactly 1 argument",
    "delete": "delete(dict, key) takes exactly 2 arguments",
    "items": "items(dict) takes exactly 1 argument",
    "merge": "merge(a, b) takes exactly 2 arguments",
    "index_of": "index_of(text, piece) takes exactly 2 arguments",
    "starts_with": "starts_with(text, prefix) takes exactly 2 arguments",
    "ends_with": "ends_with(text, suffix) takes exactly 2 arguments",
    "ord": "ord(x) takes exactly 1 argument",
    "chr": "chr(x) takes exactly 1 argument",
    "set_of": "set_of(list) takes exactly 1 argument",
    "union": "union(a, b) takes exactly 2 arguments",
    "intersect": "intersect(a, b) takes exactly 2 arguments",
    "difference": "difference(a, b) takes exactly 2 arguments",
    "fail": "fail(message) takes exactly 1 argument",
    "format": "format(text, values...) takes one or more arguments — "
              "like format(\"x={0}\", x)",
    "pad_left": "pad_left(text, width) takes exactly 2 arguments",
    "pad_right": "pad_right(text, width) takes exactly 2 arguments",
    "center": "center(text, width) takes exactly 2 arguments",
    "split_lines": "split_lines(text) takes exactly 1 argument",
    "join_lines": "join_lines(lines) takes exactly 1 argument",
    "read_file": "read_file(path) takes exactly 1 argument",
    "write_file": "write_file(path, text) takes exactly 2 arguments",
    "append_file": "append_file(path, text) takes exactly 2 arguments",
    "read_lines": "read_lines(path) takes exactly 1 argument",
    "write_lines": "write_lines(path, lines) takes exactly 2 arguments",
    "file_exists": "file_exists(path) takes exactly 1 argument",
    "file_size": "file_size(path) takes exactly 1 argument",
    "delete_file": "delete_file(path) takes exactly 1 argument",
    "list_dir": "list_dir(path) takes exactly 1 argument",
    "make_dir": "make_dir(path) takes exactly 1 argument",
    "delete_dir": "delete_dir(path) takes exactly 1 argument",
    "to_json": "to_json(value) takes exactly 1 argument",
    "from_json": "from_json(text) takes exactly 1 argument",
}


def check_arity(name, count):
    """The exact error message for a wrong argument count — None when fine.

    The checker calls this before a program runs; the interpreter calls
    it at every builtin call. Same table, same message, everywhere.
    """
    low, high = BUILTIN_ARITY[name]
    if count < low or (high is not None and count > high):
        return BUILTIN_HINT[name]
    return None
