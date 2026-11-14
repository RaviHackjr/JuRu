"""JuRu Step 2 tests — Parser (AST) + parse-time semantic checks + alignment."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from juru.lexer import Lexer, JuRuGalti, KEYWORDS
from juru.parser import Parser, Program, dump, parse_source

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


def tree(src):
    return dump(parse_source(src))


def expect_galti(src, fragment):
    try:
        parse_source(src)
    except JuRuGalti as err:
        assert fragment in err.message, "wrong message: " + err.message
        return
    raise AssertionError("expected an error, but the code parsed fine")


# ---------- expressions + precedence ----------

def t_add_first():
    assert tree("1 + 2") == "(program (expr (+ (num 1) (num 2))))"


def t_mul_binds_tighter():
    assert tree("1 + 2 * 3") == "(program (expr (+ (num 1) (* (num 2) (num 3)))))"


def t_parens_grouping():
    assert tree("(1 + 2) * 3") == "(program (expr (* (+ (num 1) (num 2)) (num 3))))"


def t_div_mod_left_assoc():
    assert tree("10 / 2 % 3") == "(program (expr (% (/ (num 10) (num 2)) (num 3))))"


def t_deep_precedence():
    assert tree("1 + 2 * 3 - 4 / 2 % 3") == \
        "(program (expr (- (+ (num 1) (* (num 2) (num 3))) (% (/ (num 4) (num 2)) (num 3)))))"


def t_unary_minus():
    assert tree("-5 + 2") == "(program (expr (+ (- (num 5)) (num 2))))"


def t_double_unary():
    assert tree("--5") == "(program (expr (- (- (num 5)))))"


def t_unary_plus():
    assert tree("+5") == "(program (expr (+ (num 5))))"


def t_add_left_assoc():
    assert tree("1 - 2 - 3") == "(program (expr (- (- (num 1) (num 2)) (num 3))))"


def t_not():
    assert tree("not true") == "(program (expr (not (bool true))))"


def t_not_double():
    assert tree("not not true") == "(program (expr (not (not (bool true)))))"


def t_and_or_precedence():
    assert tree("a or b and c") == \
        "(program (expr (or (name a) (and (name b) (name c)))))"


def t_not_binds_tighter():
    assert tree("not a and b") == \
        "(program (expr (and (not (name a)) (name b))))"


def t_compare_eq():
    assert tree("x == 10") == "(program (expr (== (name x) (num 10))))"


def t_compare_ne():
    assert tree("x != 10") == "(program (expr (!= (name x) (num 10))))"


def t_compare_le():
    assert tree("x <= 10") == "(program (expr (<= (name x) (num 10))))"


def t_compare_ge():
    assert tree("x >= 10") == "(program (expr (>= (name x) (num 10))))"


def t_compare_with_and():
    assert tree("1 < 2 and 3 >= 3") == \
        "(program (expr (and (< (num 1) (num 2)) (>= (num 3) (num 3)))))"


def t_compare_chain_error():
    expect_galti("1 < 2 < 3", "per comparison")


def t_text_plus_text():
    assert tree('"a" + "b"') == "(program (expr (+ (text a) (text b))))"


# ---------- calls, indexes, lists ----------

def t_call_simple():
    assert tree("add(1, 2)") == "(program (expr (call add (num 1) (num 2))))"


def t_call_nested():
    assert tree("f(g(1), h(2))") == \
        "(program (expr (call f (call g (num 1)) (call h (num 2)))))"


def t_call_multiline_args():
    assert tree("add(\n 1,\n 2\n)") == \
        "(program (expr (call add (num 1) (num 2))))"


def t_index():
    assert tree("a[0]") == "(program (expr (index (name a) (num 0))))"


def t_index_chain():
    assert tree("a[0][1]") == \
        "(program (expr (index (index (name a) (num 0)) (num 1))))"


def t_index_multiline():
    assert tree("a[\n 0\n]") == "(program (expr (index (name a) (num 0))))"


def t_call_then_index():
    assert tree("f(1)[0]") == \
        "(program (expr (index (call f (num 1)) (num 0))))"


def t_list_literal():
    assert tree("[1, 2, 3]") == \
        "(program (expr (list (num 1) (num 2) (num 3))))"


def t_list_nested():
    assert tree("[[1, 2], [3, 4]]") == \
        "(program (expr (list (list (num 1) (num 2)) (list (num 3) (num 4)))))"


def t_list_empty():
    assert tree("[]") == "(program (expr (list)))"


def t_list_mixed():
    assert tree('[1, "two", true, null]') == \
        "(program (expr (list (num 1) (text two) (bool true) (null))))"


def t_list_multiline():
    assert tree("a = [\n 1,\n 2\n]") == \
        "(program (assign a (list (num 1) (num 2))))"


# ---------- simple statements ----------

def t_assign():
    assert tree("x = 1 + 2") == "(program (assign x (+ (num 1) (num 2))))"


def t_assign_continuation():
    assert tree("x = 1 +\n2") == "(program (assign x (+ (num 1) (num 2))))"


def t_bools():
    assert tree("x = true\ny = false") == \
        "(program (assign x (bool true)) (assign y (bool false)))"


def t_null_assign():
    assert tree("x = null") == "(program (assign x (null)))"


def t_say():
    assert tree('say("hi")') == "(program (say (text hi)))"


def t_say_multi_args():
    assert tree('say("a", "b")') == "(program (say (text a) (text b)))"


def t_say_multiline_args():
    assert tree('say("a",\n   "b")') == "(program (say (text a) (text b)))"


def t_say_expr_args():
    assert tree("say(1 + 2, x)") == "(program (say (+ (num 1) (num 2)) (name x)))"


def t_number_statement():
    assert tree("10") == "(program (expr (num 10)))"


def t_text_statement():
    assert tree('"hi"') == "(program (expr (text hi)))"


def t_bool_statement():
    assert tree("true") == "(program (expr (bool true)))"


def t_null_statement():
    assert tree("null") == "(program (expr (null)))"


def t_empty_program():
    assert tree("") == "(program)"


def t_comment_only():
    assert tree("# only a comment") == "(program)"


def t_blank_lines():
    assert tree("\n\n\n") == "(program)"


# ---------- if / else if / else ----------

def t_if_then():
    src = "if x > 5 {\n  say(1)\n}"
    assert tree(src) == "(program (if (> (name x) (num 5)) (then (say (num 1)))))"


def t_if_else():
    src = 'if x > 5 {\n  say("big")\n} else {\n  say("small")\n}'
    assert tree(src) == \
        "(program (if (> (name x) (num 5)) (then (say (text big))) " \
        "(else (then (say (text small))))))"


def t_if_empty():
    assert tree("if true { }") == "(program (if (bool true) (then)))"


def t_else_if_chain():
    src = 'if x > 5 {\n say("a")\n} else if x == 5 {\n say("b")\n} else {\n say("c")\n}'
    assert tree(src) == \
        "(program (if (> (name x) (num 5)) (then (say (text a))) " \
        "(else (if (== (name x) (num 5)) (then (say (text b))) " \
        "(else (then (say (text c))))))))"


def t_if_nested_in_for():
    src = "for i from 1 to 3 {\n  if i > 1 {\n    say(i)\n  }\n}"
    assert tree(src) == \
        "(program (for i (num 1) (num 3) (then (if (> (name i) (num 1)) " \
        "(then (say (name i)))))))"


# ---------- while / for ----------

def t_while():
    assert tree("while x > 0 { x = x - 1 }") == \
        "(program (while (> (name x) (num 0)) (then (assign x (- (name x) (num 1))))))"


def t_for():
    assert tree("for i from 1 to 5 { say(i) }") == \
        "(program (for i (num 1) (num 5) (then (say (name i)))))"


def t_for_expr_bounds():
    assert tree("for i from 2 * 1 to 3 + 1 { }") == \
        "(program (for i (* (num 2) (num 1)) (+ (num 3) (num 1)) (then)))"


def t_nested_for():
    src = "for i from 1 to 2 {\n  for j from 1 to 2 {\n    say(i + \"-\" + j)\n  }\n}"
    assert tree(src) == \
        "(program (for i (num 1) (num 2) (then (for j (num 1) (num 2) " \
        "(then (say (+ (+ (name i) (text -)) (name j))))))))"


# ---------- break / continue ----------

def t_break_parse():
    assert tree("for i from 1 to 3 { break }") == \
        "(program (for i (num 1) (num 3) (then (break))))"


def t_continue_parse():
    assert tree("while true { continue }") == \
        "(program (while (bool true) (then (continue))))"


def t_break_inside_if_in_loop():
    src = "while true {\n  if true {\n    break\n  }\n}"
    assert tree(src) == \
        "(program (while (bool true) (then (if (bool true) (then (break))))))"


def t_err_break_outside():
    expect_galti("break", "only works inside a loop")


def t_err_continue_outside():
    expect_galti("continue", "only works inside a loop")


def t_err_return_outside():
    expect_galti("return 5", "only works inside a func")


# ---------- funcs + return ----------

def t_return_parse():
    src = "func f() {\n  return 5\n}"
    assert tree(src) == "(program (func f (params) (then (return (num 5)))))"


def t_return_empty():
    src = "func f() {\n  return\n}"
    assert tree(src) == "(program (func f (params) (then (return))))"


def t_func_params():
    src = "func add(a, b) {\n  return a + b\n}"
    assert tree(src) == \
        "(program (func add (params a b) (then (return (+ (name a) (name b))))))"


def t_func_no_params():
    src = 'func hello() {\n  say("hi")\n}\nhello()'
    assert tree(src) == \
        "(program (func hello (params) (then (say (text hi)))) (expr (call hello)))"


def t_func_multiline_params():
    src = "func f(\n a,\n b\n) {\n}"
    assert tree(src) == "(program (func f (params a b) (then)))"


def t_nested_func():
    src = "func outer() {\n  func inner() {\n    return 1\n  }\n  return inner()\n}"
    assert tree(src) == \
        "(program (func outer (params) (then (func inner (params) " \
        "(then (return (num 1)))) (return (call inner)))))"


# ---------- item assignment ----------

def t_setindex():
    src = "a = [1, 2]\na[1] = 9"
    assert tree(src) == \
        "(program (assign a (list (num 1) (num 2))) (setindex (name a) (num 1) (num 9)))"


def t_setindex_nested():
    src = "grid = [[1, 2], [3, 4]]\ngrid[1][0] = 7"
    assert tree(src) == \
        "(program (assign grid (list (list (num 1) (num 2)) (list (num 3) (num 4)))) " \
        "(setindex (index (name grid) (num 1)) (num 0) (num 7)))"


# ---------- errors (friendly, English) ----------

def t_err_eq_in_condition():
    expect_galti("if x = 5 { }", "for comparison write '=='")


def t_err_missing_brace():
    expect_galti("if x > 5 say(1)", "expected '{'")


def t_err_missing_from():
    expect_galti("for i 1 to 5 { }", "expected 'from'")


def t_err_missing_to():
    expect_galti("for i from 1 5 { }", "expected 'to'")


def t_err_for_no_end():
    expect_galti("for i from 1 to\n", "expected a value here")


def t_err_keyword_fn_name():
    expect_galti("func if() { }", "cannot be a name")


def t_err_keyword_loop_var():
    expect_galti("for while from 1 to 5 { }", "cannot be a name")


def t_err_say_no_parens():
    expect_galti('say "hi"', "write say(...)")


def t_err_expr_assign():
    expect_galti("x + 1 = 5", "'=' cannot follow an expression")


def t_err_two_on_line():
    expect_galti("10 20", "one statement per line")


def t_err_names_on_line():
    expect_galti("x y", "one statement per line")


def t_err_stray_brace():
    expect_galti("}", "without a '{'")


def t_err_stray_else():
    expect_galti("else { }", "'else' needs a matching 'if'")


def t_err_unterminated_block():
    expect_galti("if x > 5 {", "never closed")


def t_err_unclosed_paren():
    expect_galti('say("hi"', "',' or ')'")


def t_err_unclosed_list():
    expect_galti("[1, 2", "',' or ']'")


def t_err_missing_value():
    expect_galti("x ==", "the code ended")


def t_err_say_as_value():
    expect_galti("x = say(1)", "say is a statement")


def t_err_else_inside_block():
    src = "if x > 5 {\n  say(1)\n else {\n}"
    expect_galti(src, "close '}' first")


def t_err_keyword_as_value():
    expect_galti("x = if", "cannot be used as a name or a value")


def t_err_from_standalone():
    expect_galti("from 1 to 5", "'from' only works inside")


def t_err_and_first():
    expect_galti("and x", "'and' joins two things")


def t_err_call_nonname():
    expect_galti("(1 + 2)(3)", "'(' needs a name before it")


# ---------- advanced coverage ----------

def t_deep_nested_expr():
    assert tree("1 + (2 * (3 - (4 / 2)))") == \
        "(program (expr (+ (num 1) (* (num 2) (- (num 3) (/ (num 4) (num 2)))))))"


def t_mixed_bool_math():
    assert tree("a + 1 < b * 2 and not c") == \
        "(program (expr (and (< (+ (name a) (num 1)) (* (name b) (num 2))) " \
        "(not (name c)))))"


def t_long_add_chain():
    assert tree("1 + 2 + 3 + 4 + 5") == \
        "(program (expr (+ (+ (+ (+ (num 1) (num 2)) (num 3)) (num 4)) (num 5))))"


def t_return_in_if_in_func():
    src = "func f(x) {\n  if x {\n    return 1\n  }\n  return 2\n}"
    assert tree(src) == \
        "(program (func f (params x) (then (if (name x) (then (return (num 1)))) " \
        "(return (num 2)))))"


def t_while_in_for_in_if():
    src = "if true {\n  for i from 1 to 2 {\n    while false {\n      say(1)\n    }\n  }\n}"
    assert tree(src) == \
        "(program (if (bool true) (then (for i (num 1) (num 2) (then (while " \
        "(bool false) (then (say (num 1)))))))))"


def t_deep_parens_50():
    """50 levels of grouping collapse into one number node."""
    src = "(" * 50 + "1" + ")" * 50
    assert tree(src) == "(program (expr (num 1)))"


def t_call_in_condition():
    assert tree("if f(1) > 0 { }") == \
        "(program (if (> (call f (num 1)) (num 0)) (then)))"


def t_setindex_deep_chain():
    assert tree("g[0][1][2] = 5") == \
        "(program (setindex (index (index (name g) (num 0)) (num 1)) (num 2) (num 5)))"


def t_multi_func_program():
    src = ("func a(x) {\n  return x\n}\n"
           "func b(x) {\n  return a(x) + 1\n}\n"
           "func c(x) {\n  return b(x) * 2\n}\n"
           "say(c(3))\n")
    assert tree(src) == \
        "(program (func a (params x) (then (return (name x)))) " \
        "(func b (params x) (then (return (+ (call a (name x)) (num 1))))) " \
        "(func c (params x) (then (return (* (call b (name x)) (num 2))))) " \
        "(say (call c (num 3))))"


def t_empty_blocks_stacked():
    src = "if true { }\nwhile false { }\nfor i from 1 to 2 { }\nfunc f() { }"
    assert tree(src) == \
        "(program (if (bool true) (then)) (while (bool false) (then)) " \
        "(for i (num 1) (num 2) (then)) (func f (params) (then)))"


# ---------- alignment: lexer ↔ parser ↔ demo files ----------

def t_demo_file_alignment():
    """demo.jr parses into exactly this tree."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "examples", "demo.jr"), encoding="utf-8").read()
    expected = ("(program (assign name (text JuRu)) (assign level (num 3)) "
                "(say (+ (+ (text hello ) (name name)) (text !))) "
                "(say (+ (text Level ) (name level))) "
                "(say (+ (num 5) (num 3))) (say (/ (num 10) (num 4))) "
                "(say (% (num 7) (num 3))) (say (* (num 2.5) (num 2))) "
                "(say (- (+ (num 1) (* (num 2) (num 3))) (/ (num 4) (num 2)))))")
    assert tree(src) == expected


def t_funcs_demo_alignment():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "examples", "funcs_demo.jr"), encoding="utf-8").read()
    expected = ("(program "
                "(func factorial (params n) (then (if (<= (name n) (num 1)) "
                "(then (return (num 1)))) (return (* (name n) (call factorial "
                "(- (name n) (num 1))))))) "
                "(func fibo (params n) (then (if (<= (name n) (num 1)) "
                "(then (return (name n)))) (return (+ (call fibo (- (name n) (num 1))) "
                "(call fibo (- (name n) (num 2))))))) "
                "(say (text factorial:)) "
                "(for i (num 1) (num 7) (then (say (+ (+ (name i) (text ! = )) "
                "(call factorial (name i)))))) "
                "(say (text fibonacci:)) "
                "(for i (num 1) (num 10) (then (say (call fibo (name i))))))")
    assert tree(src) == expected


def t_token_stream_fully_consumed():
    src = ('x = 10\n'
           'say("hi", x[0], [1, 2])\n'
           'if true { while false { break } } else { }\n'
           'for i from 1 to 3 { }\n'
           'func f(a) { return a }\n'
           'f(true)\n'
           '1 + 2 * 3 - 4 / 5 % 6\n'
           'not x and x or false\n')
    p = Parser(Lexer(src).tokenize())
    t = p.parse()
    assert isinstance(t, Program)
    assert p.i == len(p.toks) - 1, "parser did not consume every token"


def t_lexer_error_passthrough():
    expect_galti('x = "abc', 'missing closing "')


def t_all_19_keywords_program():
    src = ('func mix(a) {\n'
           '  if a and not false or null == null {\n'
           '    for i from 0 to 2 {\n'
           '      if i == 1 {\n'
           '        continue\n'
           '      }\n'
           '      while false {\n'
           '        break\n'
           '      }\n'
           '    }\n'
           '  } else {\n'
           '    say("no")\n'
           '  }\n'
           '  return true\n'
           '}\n'
           'say(mix(true))\n')
    t = parse_source(src)
    assert isinstance(t, Program)
    assert len(KEYWORDS) == 19
    assert t.stmts[0].name == "mix"
    assert t.stmts[1].args[0].name == "mix"


def t_hinglish_names_ok():
    """Old Hinglish words are ordinary names — old code still parses as names."""
    src = "bolo = 1\nagar2 = 2\nsay(bolo + agar2)"
    assert tree(src) == \
        "(program (assign bolo (num 1)) (assign agar2 (num 2)) " \
        "(say (+ (name bolo) (name agar2))))"


def t_node_positions():
    src = "x = 5\nif true {\n  say(x)\n}"
    t = parse_source(src)
    assign = t.stmts[0]
    if_st = t.stmts[1]
    say = if_st.then[0]
    assert (assign.line, assign.col) == (1, 1)
    assert (if_st.line, if_st.col) == (2, 1)
    assert (say.line, say.col) == (3, 3)


def t_error_positions():
    try:
        parse_source("x = 1\n10 20")
    except JuRuGalti as err:
        assert err.line == 2 and err.col == 4
        return
    raise AssertionError("expected an error")


# ---------- runner ----------

TESTS = [
    t_add_first, t_mul_binds_tighter, t_parens_grouping,
    t_div_mod_left_assoc, t_deep_precedence, t_unary_minus,
    t_double_unary, t_unary_plus, t_add_left_assoc, t_not, t_not_double,
    t_and_or_precedence, t_not_binds_tighter,
    t_compare_eq, t_compare_ne, t_compare_le, t_compare_ge,
    t_compare_with_and, t_compare_chain_error, t_text_plus_text,
    t_call_simple, t_call_nested, t_call_multiline_args,
    t_index, t_index_chain, t_index_multiline, t_call_then_index,
    t_list_literal, t_list_nested, t_list_empty, t_list_mixed,
    t_list_multiline,
    t_assign, t_assign_continuation, t_bools, t_null_assign,
    t_say, t_say_multi_args, t_say_multiline_args, t_say_expr_args,
    t_number_statement, t_text_statement, t_bool_statement,
    t_null_statement, t_empty_program, t_comment_only, t_blank_lines,
    t_if_then, t_if_else, t_if_empty, t_else_if_chain, t_if_nested_in_for,
    t_while, t_for, t_for_expr_bounds, t_nested_for,
    t_break_parse, t_continue_parse, t_break_inside_if_in_loop,
    t_err_break_outside, t_err_continue_outside, t_err_return_outside,
    t_return_parse, t_return_empty, t_func_params, t_func_no_params,
    t_func_multiline_params, t_nested_func,
    t_setindex, t_setindex_nested,
    t_err_eq_in_condition, t_err_missing_brace, t_err_missing_from,
    t_err_missing_to, t_err_for_no_end, t_err_keyword_fn_name,
    t_err_keyword_loop_var, t_err_say_no_parens, t_err_expr_assign,
    t_err_two_on_line, t_err_names_on_line, t_err_stray_brace,
    t_err_stray_else, t_err_unterminated_block, t_err_unclosed_paren,
    t_err_unclosed_list, t_err_missing_value, t_err_say_as_value,
    t_err_else_inside_block, t_err_keyword_as_value, t_err_from_standalone,
    t_err_and_first, t_err_call_nonname,
    t_demo_file_alignment, t_funcs_demo_alignment,
    t_token_stream_fully_consumed, t_lexer_error_passthrough,
    t_all_19_keywords_program, t_hinglish_names_ok,
    t_node_positions, t_error_positions,
    t_deep_nested_expr, t_mixed_bool_math, t_long_add_chain,
    t_return_in_if_in_func, t_while_in_for_in_if, t_deep_parens_50,
    t_call_in_condition, t_setindex_deep_chain, t_multi_func_program,
    t_empty_blocks_stacked,
]

for test in TESTS:
    check(test.__name__, test)

passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = [r for r in RESULTS if not r[1]]

print()
print("=" * 50)
print("JuRu Step 2 (Parser): {} pass, {} fail / {} total".format(
    passed, len(failed), len(RESULTS)))
if failed:
    print()
    for name, _, msg in failed:
        print(name + ": " + msg)
    sys.exit(1)
print("Step 2 Parser: ALL PASS ✅")
sys.exit(0)
