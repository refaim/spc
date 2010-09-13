# -*- coding: utf-8 -*-

from common.functions import *
from token import tt, keywords

lexems_str = { tt.identifier: "Identifier", tt.kwInteger: "Integer",
               tt.kwReal: "Real", tt.char_const: "Character constant",
               tt.string_const: "String constant",

               tt.lparen: "Left parenthesis", tt.semicolon: "Semicolon",
               tt.rparen: "Right parenthesis", tt.colon: "Colon",
               tt.lbracket: "Left bracket", tt.rbracket: "Right bracket",
               tt.comma: "Comma", tt.double_dot: "Double dot",
               tt.caret: "Caret",

               tt.plus: "Plus", tt.less: "Less", tt.assign: "Assignment",
               tt.minus: "Minus", tt.mul: "Asterix", tt.div: "Div",
               tt.greater_or_equal: "Greater or equal", tt.dot: "Dot",
               tt.less_or_equal: "Less or equal", tt.not_equal: "Not equal",
               tt.greater: "Greater", tt.equal: "Equal",
               tt.shr: "Right shift", tt.shl: "Left shift",
               tt.logic_not: "Not", tt.logic_and: "And", tt.logic_or: "Or",
               tt.logic_xor: "Xor",
               tt.int_div: "Integer div", tt.int_mod: "Integer mod"
             }

def get_string_repr(lexem):
    if lexem in lexems_str:
        return lexems_str[lexem]
    s = str(lexem).lower().replace('kw', '')
    if s in keywords:
        if lexem not in (tt.kwReal, tt.kwInteger):
            s = "{0} (keyword)".format(s)
        return s.capitalize()
    return ''

space = " "
indent_len = 2
indent = indent_len * space
b_horz, b_vert, b_cross = "-", "|", "+"

def print_tokens(tokens):

    if empty(tokens):
        return

    headers = ["Line, pos", "Token text", "Token value", "Token type"]
    colcount = len(headers)

    # разделители + пустые строки + заголовок + основной массив
    rowcount = 3 + 4 + 1 + len(tokens)

    # номера строк
    empty_lines = [1, 3, 5, 5 + len(tokens) + 1]
    borders = [0, 4, rowcount - 1]
    header = 2

    # перед токенами два разделителя, три пустых строки и заголовок
    tokens_shift = (len(empty_lines) - 1) + (len(borders) - 1) + 1

    lp_template = "{0}, {1}"
    def values(tok):
        return [lp_template.format(tok.line, tok.pos), tok.text, str(tok.value), get_string_repr(tok.type)]

    def print_line(out, row, col):
        left_border = b_vert if col == 0 else ""
        left, right = left_border + indent, indent + b_vert
        emptyline = left + max_value_lens[col] * space + right

        if row in borders:
            length = max_value_lens[col] + len(left + right)
            right_border = b_cross if col == colcount - 1 else ""
            out[row] += b_cross + b_horz * (length - len(left_border + b_vert)) + right_border
        elif row in empty_lines:
            out[row] += emptyline
        elif row == header:
            a, b = max_value_lens[col], len(headers[col])
            lshift = (a - b) // 2 if a > b else 0
            rshift = max_value_lens[col] - len(headers[col]) - lshift
            out[row] += left + space * lshift + headers[col] + space * rshift + right
        else:
            tok = tokens[row - tokens_shift]
            value = values(tok)[col]
            rshift = max_value_lens[col] - len(value)
            out[row] += left + value + space * rshift + right

    max_value_lens = [0] * colcount

    for tok in tokens:
        for i in xrange(colcount):
            max_value_lens[i] = max(len(headers[i]), len(values(tok)[i]), max_value_lens[i])

    out = [""] * rowcount

    for row in xrange(rowcount):
        for col in xrange(colcount):
            print_line(out, row, col)

    for s in out:
        print(s)
