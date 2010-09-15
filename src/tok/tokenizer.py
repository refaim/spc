# -*- coding: utf-8 -*-

import re
import string

from common.errors import *
from common.functions import *
from token import Token, tt, special, reverse_special, keywords

class Tokenizer(object):
    def __init__(self, program):
        self._token = None
        self.eof = False
        self._file = program
        self._cline, self._cpos = -1, -1
        self._text = self._getline()
        self._tokenpos = 0, 0
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
            ch = self._getch()
            if ch.isspace(): continue
            self._tokenpos = self._cline + 1, self._cpos + 1

            if ch in string.letters + "_": tok = self._read_identifier(ch)
            elif ch in string.digits + "$": tok = self._read_number(ch)
            elif ch == "/": tok = self._read_comment(ch)
            elif ch in "{(": tok = self._read_block_comment(ch)
            elif ch == "'": tok = self._read_string_const(ch)
            elif ch == "#": tok = self._read_char_const(ch)
            elif ch in special:
                tok = self._read_delimiter(ch)
            elif nonempty(ch):
                raise_exception(IllegalCharError((self._tokenpos), [ch]))

            found = not (empty(ch) or tok is None)

        if not found or empty(ch):
            tok = Token(tt.eof, value='EOF')
        tok.line, tok.pos = self._tokenpos
        self._token = tok

    def _read_number(self, ch):
        ttype = tt.integer
        if ch == '$':
            # hex
            numstring = self._match_regexp(r'(\$[\da-fA-F]*)')
            if numstring == '$':
                numstring = ''
            else:
                value = eval('0x' + numstring[1:])
        else:
            # try real
            numstring = self._match_regexp(r'(\d+\.\d+)|(\d+[Ee]-{0,1}\d+)')
            # try int
            if empty(numstring):
                numstring = self._match_regexp(r'\d+')
                value = int(numstring)
                # check for real
                if self._getch() in '.eE':
                    if self._getch() != '.':
                        numstring = ''
                        ttype = tt.real
                    self._putch()
                self._putch()
            else:
                 ttype, value = tt.real, eval(numstring)

        etypes = { tt.integer: IntError, tt.real: RealError }
        if empty(numstring):
            raise_exception(etypes[ttype](self._tokenpos))
        return Token(ttype, numstring, value)

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
        if both in special:
            text, ttype = both, tt.__dict__[special[both]]
        else:
            text, ttype = first, tt.__dict__[special[first]]
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
            value = '"' + s[1:-1].replace("''", "'") + '"'
            return Token(tt.string_const, s, value)
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
        if value in keywords:
            ttype = tt.__dict__['kw' + value.capitalize()]
        elif value in special:
            ttype = tt.__dict__[special[value]]
        elif value in tt:
            ttype = tt.__dict__[value]
        else:
            ttype = tt.identifier
        return Token(ttype, name, value)

    def _read_char_const(self, ch):
        char = self._match_regexp(r'(#\d*)').lstrip('#')
        if empty(char) or int(char) > 255:
            raise_exception(CharConstError(self._tokenpos))
        return Token(tt.char_const, '#' + char, chr(int(char)))
