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

    def _getch(self):
        self._cpos += 1
        if not self.eof and self._cpos == len(self._text):
            self._text = self._getline()
        return self._text[self._cpos] if not self.eof else ""

    def _getline(self):
        line = self._file.readline()
        self._cline, self._cpos = self._cline + 1, -1
        self.eof = empty(line)
        if not self.eof and last(line) != '\n':
           line += '\n'
        return line

    def _putch(self, count=1):
        self._cpos -= count

    def get_token(self):
        return self._token

    def next_token(self):
        found = False
        while not found and not self.eof:
            #self._match_regexp(r'(\s+|\\\n)+')
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
            elif not empty(ch):
                raise_exception(IllegalCharError((self._tokenpos), [ch]))

            found = not (empty(ch) or tok is None)

        if found and not empty(ch):
            tok.line, tok.pos = self._tokenpos
            self._token = tok
        else:
            self._token = Token(tt.eof, value='EOF')

    def _read_number(self, ch):
        ttype = tt.integer
        if ch == '$':
            num = self._match_regexp(r'(\$[\da-fA-F]*)')
        else:
            num = self._match_regexp(r'(\d+\.\d+)|(\d+[Ee]-{0,1}\d+)')
            if not empty(num):
                ttype = tt.float
            else:
                num = self._match_regexp(r'\d+')
                if self._getch() in '.eE':
                    if self._getch() != '.':
                        num, ttype = '', tt.float
                    self._putch()
                self._putch()
        etypes = { tt.integer: IntError, tt.float: FloatError }
        if empty(num) or num == '$':
            raise_exception(etypes[ttype](self._tokenpos))
        return Token(ttype, num)

    def _read_comment(self, ch):
        if self._getch() == '/':
            self._text = self._getline()
            return None
        else:
            self._putch()
            return self._read_delimiter(ch)

    def _read_block_comment(self, ch):
        # first - {}, second - (**)

        def read_first(ch):
            while ch not in ('}', ''):
                ch = self._getch()
            if ch == '}': return None
            raise_exception(BlockCommentEofError(self._tokenpos))

        def read_second(ch):
            if self._getch() != '*':
                self._putch()
                return self._read_delimiter(ch)
            found = False
            while not (found or empty(ch)):
                ch = self._getch()
                if ch == '*':
                    found = self._getch() == ')'
            if found: return None
            raise_exception(BlockCommentEofError(self._tokenpos))

        methods = [read_first, read_second]
        return methods[ch == '('](ch)

    def _read_delimiter(self, ch):
        first, both = ch, ch + self._getch()
        chars = dict(delimiters.items() + operations.items())
        if both in chars:
            text, ttype = both, chars[both]
        else:
            text, ttype = first, chars[first]
            self._putch()
        return Token(ttype, text)

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
            return Token(tt.string_const, s)
        else:
            raise_exception(StringEofError(self._tokenpos))

    def _match_regexp(self, pattern):
        match = re.compile(pattern).match(self._text, self._cpos)
        if match is None:
            return ''
        match = match.group(0)
        self._cpos += len(match) - 1
        return match

    def _read_identifier(self, ch):
        name = self._match_regexp(r'(\w+)')
        value = name.lower()
        ttype = subscript(keywords, value) or subscript(operations, value) or \
            tt.identifier
        return Token(ttype, name, value)

    def _read_char_const(self, ch):
        char = self._match_regexp(r'(#\d*)').lstrip('#')
        if empty(char) or int(char) > 255:
            raise_exception(CharConstError(self._tokenpos))
        return Token(tt.char_const, '#' + char, chr(int(char)))
