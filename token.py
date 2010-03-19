# -*- coding: utf-8 -*-

from string import printable
from sys import path as syspath

from enum import Enum

tt = Enum("identifier", "integer", "real", "char_const", "string_const", "eof")

keywords = {}
kw = Enum("array", "begin", "break", "const", "continue", "do", "else", "end",\
          "real", "for", "function", "if", "integer", "procedure", "record",\
          "repeat", "then", "until", "var", "while")
for elm in kw:
    keywords[str(elm)] = elm

operations = {}
ops = ["+", "-", "*", "/", "=", "<>", "<", ">", "<=", ">=", ":=", ".", "and",\
       "or", "xor", "not", "shr", "shl", "div", "mod"]
op = Enum("plus", "minus", "mul", "div", "equal", "not_equal", "lesser",\
          "greater", "lesser_or_equal", "greater_or_equal", "assign", "dot",\
          "logic_and", "logic_or", "logic_xor", "logic_not", "shr", "shl",\
          "int_div", "int_mod")
for i in xrange(len(ops)):
    operations[ops[i]] = op[i]
del ops

delimiters = {}
ds = [";", ":", ",", "..", "(", ")", "[", "]", "^"]
dlm = Enum("semicolon", "colon", "comma", "double_dot", "lparen", "rparen",\
           "lbracket", "rbracket", "caret")
for i in xrange(len(ds)):
    delimiters[ds[i]] = dlm[i]
del ds

class Token(object):
    def __init__(self, type=None, text="", value=""):
        self.type, self.text, self.value = type, text, value
        self.line, self.pos = -1, -1

    @property
    def linepos(self):
        return (self.line, self.pos)
