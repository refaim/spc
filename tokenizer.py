# -*- coding: utf-8 -*-

from string import printable, digits, hexdigits

from constants import *
from errors import raise_exception, BlockCommentEofError, StringEofError

class Token:
    def __init__(self, type = None, text = "", value = "", line = 0, pos = 0, error = False):
        self.error = error
        self._type, self.text = type, text
        self._setval(value)
        self.line, self.pos = line, pos

    def _getval(self):        
        return self._value              

    def _setval(self, v):

        def make_string(text):
            return '"{0}"'.format(text[1:len(text)-1].replace("''", "'"))
        def make_char(c):
            return c if c in printable else c.encode("cp1251")
        def make_int(n):
            return eval(n.replace("$", "0x")) if n.startswith("$") else int(n)

        value_makers = { tt_string_const: make_string, tt_char_const: make_char, 
                         tt_float: eval, tt_integer: make_int }

        if not self.error and self.type in value_makers:
            if v == "": v = self.text
            self._value = value_makers[self.type](v)
        else: 
            self._value = ""

    def _gettype(self):
        return tt_wrong if self.error else self._type

    def _settype(self, t):
        self._type = t

    def _geterrmsg(self):
        return error_msg[self._type] if self.error else ""

    value = property(_getval, _setval)
    type = property(_gettype, _settype)
    errmsg = property(_geterrmsg)

class Tokenizer:
    def __init__(self, program):
        self._token = None
        self._eof = False
        self._file = program
        self._cline, self._cpos = -1, -1
        self._text = self._getline()
        self.next_token()

    def _getline(self):
        line = self._file.readline()
        self._cline += 1
        self._eof = line == ""
        if not self._eof:
            if line[len(line) - 1] != '\n':
                line += '\n'
        self._cpos = -1
        return line

    def _getch(self):
        self._cpos += 1
        if not self._eof and self._cpos == len(self._text):
            self._text = self._getline()
        return self._text[self._cpos] if not self._eof else ""

    def _putch(self, count = 1):
        self._cpos -= count

    @property
    def curfilepos(self):
        if not self._eof:
            return (self._cline + 1, self._cpos + 1)
        else:
            return None
            
    def get_token(self):       
        return self._token

    def next_token(self):
        found = False
        ch = 1
        while not found and not self._eof:
            ch = self._getch()
            if ch.isspace(): continue
            line, pos = self._cline + 1, self._cpos + 1

            if ch.isalpha() or ch == "_": tok = self._read_identifier(ch)
            elif ch.isdigit() or ch == "$": tok = self._read_number(ch)
            elif ch == "/": tok = self._read_comment(ch)
            elif ch in ["{", "("]: tok = self._read_block_comment(ch)
            elif ch == "'": tok = self._read_string_const(ch)
            elif ch == "#": tok = self._read_char_const(ch)
            elif ch in delimiters: tok = self._read_delimiter(ch)
            else: tok = Token(type = tt_unknown, text = ch, error = True)
            
            found = tok != None

        if found and ch != "": 
            tok.line, tok.pos = line, pos 
            self._token = tok
        else:
            self._token = None

    def _read_identifier(self, ch):
        s, ch = ch, self._getch()
        while ch.isalnum() or ch == "_":
            s, ch = s + ch, self._getch()
        ttype = tt_keyword if s.lower() in keywords else tt_identifier
        self._putch()
        return Token(type = ttype, text = s)
        
    def _read_number(self, ch):       
        float_part = ".eE"
        valid_chars = { tt_hex: hexdigits, tt_integer: digits, tt_float: digits + float_part }

        num, ch = [ch], self._getch()
        ttype = tt_hex if num == ["$"] else (tt_float if ch in float_part else tt_integer)
        while ch and ch in valid_chars[ttype]:

            # десятичная точка, минус или экспонента могут встретиться только один раз
            if ttype == tt_float and ch in float_part: 
                valid_chars[ttype] = valid_chars[ttype].replace(ch.lower(), "").replace(ch.upper(), "")

            num.append(ch)
            ch = self._getch()

            if ttype != tt_hex and ch in float_part: 
                ttype = tt_float
                valid_chars[ttype] += "-"

        num = "".join(c for c in num)
        matches = numerical_regexps[ttype].findall(num)
        error = not (matches and "".join(matches[0]).startswith(num))
        self._putch()

        if ttype == tt_hex:
            ttype = tt_integer

        return Token(type = ttype, text = num, error = error)

    def _read_comment(self, ch):
        if ch == self._getch():
            self._text = self._getline()
            return None
        else:
            self._putch()
            return self._read_delimiter(ch)

    def _read_block_comment(self, ch):       
        # first - {}, second - (**)
        filepos = self.curfilepos

        def read_first(ch):
            ch = self._getch()
            while ch != "}" and ch:
                ch = self._getch()
            if ch == "}": return None
            raise_exception(BlockCommentEofError(filepos))

        def read_second(ch):
            if self._getch() != "*":
                self._putch()
                return self._read_delimiter(ch)
            ch = self._getch()
            found = False
            while not found and ch:
                ch = self._getch()
                if ch == "*":
                    found = self._getch() == ")"
            if found: return None 
            raise_exception(BlockCommentEofError(filepos))

        methods = [read_first, read_second]
        return methods[ch == "("](ch)

    def _read_delimiter(self, ch):
        first, second = ch, self._getch()
        possible = first + second
        text = possible if possible in delimiters else first
        if text == first: self._putch()
        return Token(type = delimiters[text], text = text)
  
    def _read_string_const(self, ch):
        filepos = self.curfilepos
        s, ch = [ch], self._getch()
        s_end = False
        line = self._cline
        while not s_end and not self._eof:
            if ch == "'":
                pos = self._cpos
                while ch == "'": ch = self._getch()
                ap_count = self._cpos - pos
                s.append("'" * ap_count) 
                if ap_count % 2 != 0:
                    s_end = True
                    self._putch()
                continue
            s.append(ch)
            ch = self._getch()
        if s_end and line == self._cline:
            s = "".join(c for c in s)
            return Token(type = tt_string_const, text = s)
        else:
            raise_exception(StringEofError(filepos))

    def _read_char_const(self, ch):
        s, ch = [ch], self._getch()
        while ch.isdigit():
            s.append(ch)
            ch = self._getch()
        s = "".join(c for c in s)
        error = False
        try:
            ch = chr(int(s[1:]))
        except ValueError:
            error = True
        self._putch()
        return Token(type = tt_char_const, text = s, value = ch, error = error)
