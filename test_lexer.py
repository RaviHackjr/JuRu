"""JuRu Step 1 tests — Lexer (source text → tokens)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import (
    Lexer, JuRuGalti,
    NUMBER, TEXT, NAME, KEYWORD, OPERATOR, NEWLINE, EOF, KEYWORDS,
)

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print("PASS  " + name)
    except AssertionError as e:
        RESULTS.append((name, False, "FAIL: " + str(e)))
        print("FAIL  " + name + " -> " + str(e))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False, "ERROR: " + repr(e)))
        print("ERROR " + name + " -> " + repr(e))


def toks(src):
    return Lexer(src).tokenize()


def pairs(src):
    return [(t.type, t.value) for t in toks(src)]


def EOF_T():
    return (EOF, "<end>")


def expect_galti(src, fragment):
    try:
        toks(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected an error, but the code lexed fine")


# ---------- basics ----------

def t_empty():
    assert pairs("") == [EOF_T()]


def t_blank_lines():
    assert pairs("\n\n\n") == [EOF_T()]


def t_single_newline():
    assert pairs("\n") == [EOF_T()]


# ---------- numbers ----------

def t_number_int():
    assert pairs("10") == [(NUMBER, "10"), EOF_T()]


def t_number_float():
    assert pairs("3.14") == [(NUMBER, "3.14"), EOF_T()]


def t_number_zero_float():
    assert pairs("0.5") == [(NUMBER, "0.5"), EOF_T()]


def t_number_big():
    assert pairs("999999999") == [(NUMBER, "999999999"), EOF_T()]


def t_dot_without_digits():
    expect_galti("1.", "digits are needed after the dot")


def t_two_dots():
    expect_galti("1.2.3", "only one dot")


def t_leading_dot():
    expect_galti(".5", "no leading")


def t_number_then_name():
    assert pairs("12abc") == [(NUMBER, "12"), (NAME, "abc"), EOF_T()]


# ---------- text ----------

def t_text_basic():
    assert pairs('"hello"') == [(TEXT, "hello"), EOF_T()]


def t_text_empty():
    assert pairs('""') == [(TEXT, ""), EOF_T()]


def t_text_escapes():
    ts = toks('"a\\nb\\tc\\"d\\\\e"')
    assert ts[0].type == TEXT
    assert ts[0].value == "a\nb\tc\"d\\e"
    assert ts[1].type == EOF


def t_text_unclosed():
    expect_galti('"abc', 'missing closing "')


def t_text_bad_escape():
    expect_galti('"a\\q"', "escape")


def t_text_no_newline():
    expect_galti('"a\nb"', 'missing closing "')


def t_text_hash_inside():
    assert pairs('"a # b"') == [(TEXT, "a # b"), EOF_T()]


def t_backslash_at_end():
    expect_galti('"abc\\', "something must come after")


# ---------- names & keywords ----------

def t_names():
    assert pairs("name _x a1") == [
        (NAME, "name"), (NAME, "_x"), (NAME, "a1"), EOF_T()]


def t_keyword_like_names():
    assert pairs("saying ifx fork till") == [
        (NAME, "saying"), (NAME, "ifx"), (NAME, "fork"), (NAME, "till"), EOF_T()]


def t_unicode_names():
    assert pairs("नाम = 5") == [
        (NAME, "नाम"), (OPERATOR, "="), (NUMBER, "5"), EOF_T()]


def t_all_19_keywords():
    words = ("say if else while for from to in break continue func return "
             "true false null and or not import").split()
    assert len(words) == 19
    assert set(words) == KEYWORDS
    for w in words:
        assert pairs(w) == [(KEYWORD, w), EOF_T()]


def t_old_hinglish_now_names():
    """All old Hinglish words are plain names now — nothing reserved."""
    words = ("bolo agar warna jabtak har se tak ruk aage kaam wapas "
             "sahi galat khaali aur ya nahi dikhao").split()
    for w in words:
        assert pairs(w) == [(NAME, w), EOF_T()]


# ---------- operators ----------

def t_single_ops():
    src = "+ - * / % = < > ( ) { } [ ] ,"
    assert pairs(src) == [
        (OPERATOR, c) for c in "+-*/%=<>(){}[],"] + [EOF_T()]


def t_double_ops():
    assert pairs("== != <= >=") == [
        (OPERATOR, "=="), (OPERATOR, "!="),
        (OPERATOR, "<="), (OPERATOR, ">="), EOF_T()]


def t_assign_vs_compare():
    assert pairs("x = 1 == 2") == [
        (NAME, "x"), (OPERATOR, "="), (NUMBER, "1"),
        (OPERATOR, "=="), (NUMBER, "2"), EOF_T()]


# ---------- friendly error hints ----------

def t_bang_alone():
    expect_galti("!", "'!' alone does not work")


def t_ampersand():
    expect_galti("a & b", "use 'and' instead of '&'")


def t_pipe():
    expect_galti("a | b", "use 'or' instead of '|'")


def t_semicolon():
    expect_galti("x = 1;", "no semicolons")


def t_colon_token():
    """':' is a real token now — dict pairs and slices use it."""
    assert pairs("a[1:2]") == [
        (NAME, "a"), (OPERATOR, "["), (NUMBER, "1"),
        (OPERATOR, ":"), (NUMBER, "2"), (OPERATOR, "]"), EOF_T(),
    ]


def t_single_quote():
    expect_galti("'hi'", "double quotes")


def t_at_sign():
    expect_galti("@", "I do not understand")


# ---------- comments ----------

def t_comment_skipped():
    assert pairs("1 # hello\n2") == [
        (NUMBER, "1"), (NEWLINE, "\n"), (NUMBER, "2"), EOF_T()]


def t_comment_at_eof():
    assert pairs("1 # hi") == [(NUMBER, "1"), EOF_T()]


# ---------- positions ----------

def t_token_positions():
    ts = toks("ab\ncd")
    assert (ts[0].line, ts[0].col) == (1, 1)      # name ab
    assert (ts[1].line, ts[1].col) == (1, 3)      # the NEWLINE token
    assert (ts[2].line, ts[2].col) == (2, 1)      # name cd


def t_newline_col_reset():
    ts = toks("  x\n  y")
    assert (ts[0].line, ts[0].col) == (1, 3)
    assert (ts[2].line, ts[2].col) == (2, 3)


def t_tab_columns():
    ts = toks("\t\tx")
    assert (ts[0].line, ts[0].col) == (1, 3)


def t_error_position():
    try:
        toks("x = 1\n!")
    except JuRuGalti as err:
        assert err.line == 2 and err.col == 1
        return
    raise AssertionError("expected an error")


# ---------- real code shapes ----------

def t_demo_line():
    assert pairs('say("hello " + "JuRu")') == [
        (KEYWORD, "say"), (OPERATOR, "("), (TEXT, "hello "),
        (OPERATOR, "+"), (TEXT, "JuRu"), (OPERATOR, ")"), EOF_T(),
    ]


def t_for_tokens():
    assert pairs("for i from 1 to 10") == [
        (KEYWORD, "for"), (NAME, "i"), (KEYWORD, "from"), (NUMBER, "1"),
        (KEYWORD, "to"), (NUMBER, "10"), EOF_T(),
    ]


def t_index_tokens():
    assert pairs("a[0]") == [
        (NAME, "a"), (OPERATOR, "["), (NUMBER, "0"), (OPERATOR, "]"), EOF_T()]


def t_nested_parens():
    assert pairs("((1))") == [
        (OPERATOR, "("), (OPERATOR, "("), (NUMBER, "1"),
        (OPERATOR, ")"), (OPERATOR, ")"), EOF_T()]


def t_block_tokens():
    assert pairs("if x { say(1) }") == [
        (KEYWORD, "if"), (NAME, "x"), (OPERATOR, "{"), (KEYWORD, "say"),
        (OPERATOR, "("), (NUMBER, "1"), (OPERATOR, ")"), (OPERATOR, "}"),
        EOF_T(),
    ]


def t_crlf_newline():
    assert pairs("1\r\n2") == [
        (NUMBER, "1"), (NEWLINE, "\n"), (NUMBER, "2"), EOF_T()]


def t_stress_many_tokens():
    src = "+".join(["1"] * 2000)
    ts = toks(src)
    assert len(ts) == 4000
    assert ts[-1].type == EOF
    assert sum(1 for t in ts if t.type == NUMBER) == 2000


# ---------- advanced coverage ----------

def t_scientific_notation():
    """Documents behavior: 1e5 is the number 1 followed by the name e5."""
    assert pairs("1e5") == [(NUMBER, "1"), (NAME, "e5"), EOF_T()]


def t_hex_like():
    """Documents behavior: 0x10 is 0 then the name x10 (no hex in JuRu)."""
    assert pairs("0x10") == [(NUMBER, "0"), (NAME, "x10"), EOF_T()]


def t_1_dot_dot_2():
    expect_galti("1..2", "digits are needed after the dot")


def t_deeply_nested_parens():
    assert pairs("((((1))))") == [
        (OPERATOR, "("), (OPERATOR, "("), (OPERATOR, "("), (OPERATOR, "("),
        (NUMBER, "1"),
        (OPERATOR, ")"), (OPERATOR, ")"), (OPERATOR, ")"), (OPERATOR, ")"),
        EOF_T()]


def t_full_op_stream():
    src = "== != <= >= + - * / % = < > ( ) { } [ ] ,"
    expected = [(OPERATOR, w) for w in src.split()] + [EOF_T()]
    assert pairs(src) == expected


def t_multiline_positions():
    ts = toks("x\n\t y\nz")
    assert (ts[0].line, ts[0].col) == (1, 1)
    assert (ts[2].line, ts[2].col) == (2, 3)   # tab + space, then y
    assert (ts[4].line, ts[4].col) == (3, 1)


def t_unclosed_text_error_position():
    try:
        toks('"ab')
    except JuRuGalti as err:
        assert err.line == 1 and err.col == 1
        assert 'missing closing "' in err.message
        return
    raise AssertionError("expected an error")


def t_text_only_quote_escape():
    src = '"' + '\\"' + '"'          # "\\"" → text holding one quote char
    assert pairs(src) == [(TEXT, '"'), EOF_T()]


# ---------- runner ----------

TESTS = [
    t_empty, t_blank_lines, t_single_newline,
    t_number_int, t_number_float, t_number_zero_float, t_number_big,
    t_dot_without_digits, t_two_dots, t_leading_dot, t_number_then_name,
    t_text_basic, t_text_empty, t_text_escapes, t_text_unclosed,
    t_text_bad_escape, t_text_no_newline, t_text_hash_inside,
    t_backslash_at_end,
    t_names, t_keyword_like_names, t_unicode_names,
    t_all_19_keywords, t_old_hinglish_now_names,
    t_single_ops, t_double_ops, t_assign_vs_compare,
    t_bang_alone, t_ampersand, t_pipe, t_semicolon, t_colon_token,
    t_single_quote, t_at_sign,
    t_comment_skipped, t_comment_at_eof,
    t_token_positions, t_newline_col_reset, t_tab_columns,
    t_error_position,
    t_demo_line, t_for_tokens, t_index_tokens, t_nested_parens,
    t_block_tokens, t_crlf_newline, t_stress_many_tokens,
    t_scientific_notation, t_hex_like, t_1_dot_dot_2,
    t_deeply_nested_parens, t_full_op_stream, t_multiline_positions,
    t_unclosed_text_error_position, t_text_only_quote_escape,
]

for test in TESTS:
    check(test.__name__, test)

passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = [r for r in RESULTS if not r[1]]

print()
print("=" * 50)
print("JuRu Step 1 (Lexer): {} pass, {} fail / {} total".format(
    passed, len(failed), len(RESULTS)))
if failed:
    print()
    for name, _, msg in failed:
        print(name + ": " + msg)
    sys.exit(1)
print("Step 1 Lexer: ALL PASS ✅")
sys.exit(0)
