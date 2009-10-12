# -*- coding: utf-8 -*-

import re

keyword_count = 20
shift = 0
kw_begin, kw_break, kw_const, kw_continue, kw_do, kw_else, kw_end, kw_float,\
kw_for, kw_function, kw_if, kw_integer, kw_nil, kw_procedure, kw_record,\
kw_repeat, kw_then, kw_until, kw_var, kw_while = range(keyword_count)

keywords = { "begin": kw_begin, "break": kw_break, "const": kw_const, "continue": kw_continue, "do": kw_do, "else": kw_else,
             "end": kw_end, "float": kw_float, "for": kw_for, "function": kw_function, "if": kw_if, "integer": kw_integer, 
             "nil": kw_nil, "procedure": kw_procedure, "record": kw_record, "repeat": kw_repeat, 
             "then": kw_then, "until": kw_until, "var": kw_var, "while": kw_while
           }

delimiters_count = 20
shift += keyword_count
tt_plus, tt_LT, tt_assign, tt_lparen, tt_EQ, tt_comma, tt_minus,\
tt_GT, tt_semicolon, tt_rparen, tt_NEQ, tt_mul, tt_LTE,\
tt_colon, tt_LSB, tt_div, tt_GTE, tt_dot, tt_RSB,\
tt_double_dot = range(shift, shift + delimiters_count)

delimiters = { "+": tt_plus,  "<" : tt_LT,  ":=": tt_assign,    "(": tt_lparen,
               "-": tt_minus, ">" : tt_GT,  ";" : tt_semicolon, ")": tt_rparen,
               "*": tt_mul,   "<=": tt_LTE, ":" : tt_colon,     "[": tt_LSB,           
               "/": tt_div,   ">=": tt_GTE, "." : tt_dot,       "]": tt_RSB,
                              "=" : tt_EQ,  "," : tt_comma,     
                              "<>": tt_NEQ, "..": tt_double_dot                                  
             }
                                                                                                 
shift += delimiters_count
common_lexems_count = 12
tt_keyword, tt_identifier, tt_dec, tt_hex, tt_float,\
tt_char_const, tt_string_const, tt_unknown, tt_error,\
tt_block_comment, tt_comment, tt_wrong = range(shift, shift + common_lexems_count)

lexems_str = { tt_keyword: "Keyword", tt_identifier: "Identifier", 
               tt_dec: "Integer (decimal)", tt_hex: "Integer (hexadecimal)", tt_float: "Float",
               tt_char_const: "Character constant", tt_string_const: "String constant",
               tt_block_comment: "Block comment", tt_comment: "Comment", tt_error: "Lexical error",
               tt_wrong: "Wrong token",

               tt_plus: "Plus",   tt_LT: "Less",              tt_assign: "Assignmnent",  tt_lparen: "Left parenthesis",
               tt_minus: "Minus", tt_GT: "Greater",           tt_semicolon: "Semicolon", tt_rparen: "Right parenthesis",
               tt_mul: "Asterix", tt_LTE: "Less or equal",    tt_colon: "Colon",         tt_LSB: "Left square bracket",
               tt_div: "Div",     tt_GTE: "Greater or equal", tt_dot: "Dot",             tt_RSB: "Right square bracket",
                                  tt_EQ: "Equal",             tt_comma: "Comma",
                                  tt_NEQ: "Not equal",        tt_double_dot: "Double dot"
             }

hex_re = re.compile(r"\$[0-9a-fA-F]+")
dec_re = re.compile(r"\d+")
float_re = re.compile(r"(\d+\.\d+)|(\d+[Ee]-{0,1}\d+)")
numerical_regexps = { tt_hex: hex_re, tt_dec: dec_re, tt_float: float_re }

generic_error = "ERROR"
error_msg = { tt_string_const: "EOF in string constant", tt_block_comment: "EOF in block comment",
              tt_hex: "Wrong hexadecimal number", tt_dec: "Wrong decimal number", tt_float: "Wrong float number",   
              tt_char_const: "Wrong character constant",
              tt_unknown: "Illegal character", tt_error: "" }
