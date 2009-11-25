# -*- coding: utf-8 -*-

from string import printable
from sys import path as syspath

from enum import Enum

keywords = {}

kw = Enum("array", "begin", "break", "const", "continue", "do", "else", "end",\
          "float", "for", "function", "if", "integer", "procedure", "record",\
          "repeat", "then", "until", "var", "while")

for elm in kw:
    keywords[str(elm)] = elm


tt = Enum("identifier", "integer", "float", "char_const", "string_const")

delimiters = {}

ds = ["+", "-", "*", "/", "=", "<>", "<", ">", "<=", ">=", ":=", ";", ":",\
      ".", ",", "..", "(", ")", "[", "]", "^"]

dlm = Enum("plus", "minus", "mul", "div", "equal", "not_equal", "lesser",\
           "greater", "lesser_or_equal", "greater_or_equal", "assign",\
           "semicolon", "colon", "dot", "comma", "double_dot", "lparen",\
           "rparen", "lbracket", "rbracket", "caret")

for i in range(len(ds)):
    delimiters[ds[i]] = dlm[i]
del ds

class Token(object):
    def __init__(self, type = None, text = "", value = "", line = -1, pos = -1, error = False):
        self._type, self.text, self.error = type, text, error
        self.line, self.pos = line, pos
        self._setval(value)

    @property
    def linepos(self):
        return (self.line, self.pos)

    def _getval(self):
        return self._value

    def _setval(self, v):

        def make_string(text):
            return '"{0}"'.format(text[1:len(text)-1].replace("''", "'"))
        def make_char(c):
            return c if c in printable else c.encode("utf-8")
        def make_int(n):
            return eval(n.replace("$", "0x")) if n.startswith("$") else int(n)

        value_makers = { tt.string_const: make_string, tt.char_const: make_char,
                         tt.float: eval, tt.integer: make_int }

        self._value = ""
        if self.type in value_makers:
            if v == "": v = self.text
            self._value = value_makers[self.type](v)
        else:
            self._value = v

    def _gettype(self):
        return self._type

    def _settype(self, t):
        self._type = t

    value = property(_getval, _setval)
    type = property(_gettype, _settype)
