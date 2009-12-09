# -*- coding: utf-8 -*-

import re
from string import digits, hexdigits, letters

from common import *
from errors import *
from token import Token, keywords, delimiters, operations, tt

class Tokenizer(object):
    def __init__(self, program):
        self._token = None
        self.eof = False
        self._file = program
        self._cline, self._cpos = -1, -1
        self._text = self._getline()
        self.next_token()

    def __iter__(self):
        while not self.eof:
            yield self.get_token()
            self.next_token()

    def _getline(self):
        line = self._file.readline()
        self._cline += 1
        self.eof = line == ""
        if not self.eof:
            if line[len(line) - 1] != '\n':
                line += '\n'
        self._cpos = -1
        return line

    def _getch(self):
        self._cpos += 1
        if not self.eof and self._cpos == len(self._text):
            self._text = self._getline()
        return self._text[self._cpos] if not self.eof else ""

    def _putch(self, count = 1):
        self._cpos -= count

    def get_token(self):
        return self._token

    def next_token(self):
        found = False
        ch = 1
        while not found and not self.eof:
            ch = self._getch()
            if ch.isspace(): continue
            self._tokenpos = self._cline + 1, self._cpos + 1

            if ch in letters + "_": tok = self._read_identifier(ch)
            elif ch in digits + "$": tok = self._read_number(ch)
            elif ch == "/": tok = self._read_comment(ch)
            elif ch in "{(": tok = self._read_block_comment(ch)
            elif ch == "'": tok = self._read_string_const(ch)
            elif ch == "#": tok = self._read_char_const(ch)
            elif ch in delimiters or ch in operations:
                tok = self._read_delimiter(ch)
            elif ch != "":
                raise_exception(IllegalCharError((self._tokenpos), [ch]))
            found = ch != "" and not tok is None

        if found and ch != "":
            tok.line, tok.pos = self._tokenpos
            self._token = tok
        else:
            self._token = Token(type = tt.eof, value = 'EOF')

    def _read_number(self, ch):
        ttype = tt.integer
        if ch == '$':
            num = self._get_match(r'(\$[\da-fA-F]*)')
        else:
            num = self._get_match(r'(\d+\.\d+)|(\d+[Ee]-{0,1}\d+)')
            if empty(num):
                num = self._get_match(r'\d+')
                if self._getch() in '.eE':
                    num, ttype = '', tt.float
                self._putch()
            else:
                ttype = tt.float
        etypes = { tt.integer: IntError, tt.float: FloatError }
        if empty(num) or num == '$':
            raise_exception(etypes[ttype](self._tokenpos))
        return Token(ttype, num)

    def _read_comment(self, ch):
        if ch == self._getch():
            self._text = self._getline()
            return None
        else:
            self._putch()
            return self._read_delimiter(ch)

    def _read_block_comment(self, ch):
        # first - {}, second - (**)

        def read_first(ch):
            ch = self._getch()
            while ch != "}" and ch:
                ch = self._getch()
            if ch == "}": return None
            raise_exception(BlockCommentEofError(self._tokenpos))

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
            raise_exception(BlockCommentEofError(self._tokenpos))

        methods = [read_first, read_second]
        return methods[ch == "("](ch)

    def _read_delimiter(self, ch):
        char_set = delimiters if ch in delimiters else operations
        first, second = ch, self._getch()
        possible = first + second
        if possible == ":=": char_set = operations
        text = possible if possible in char_set else first
        if text == first: self._putch()
        return Token(type = char_set[text], text = text)

    def _read_string_const(self, ch):
        s, ch = [ch], self._getch()
        s_end = False
        line = self._cline
        while not s_end and not self.eof:
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
            return Token(type = tt.string_const, text = s)
        else:
            raise_exception(StringEofError(self._tokenpos))

    def _get_match(self, pattern):
        match = re.compile(pattern).match(self._text, self._cpos)
        if not match is None:
            match = match.group()
            self._cpos += len(match) - 1
        return match or ''

    def _read_identifier(self, ch):
        name = self._get_match(r'(\w+)')
        value = name.lower()
        ttype = subscript(keywords, value) or subscript(operations, value) or \
            tt.identifier
        return Token(ttype, name, value)

    def _read_char_const(self, ch):
        char = self._get_match(r'(#\d*)').lstrip('#')
        if empty(char) or int(char) > 255:
            raise_exception(CharConstError(self._tokenpos))
        return Token(tt.char_const, '#' + char, chr(int(char)))
