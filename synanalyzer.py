# -*- coding: utf-8 -*-

from syn import *
from constants import *
from tokenizer import Token
from errors import raise_exception, UnexpectedTokenError, ParMismatchError

operators = [[tt_plus, tt_minus], [tt_mul, tt_div]]
max_priority = len(operators) - 1

class Parser:
    def __init__(self, tokenizer):
        self._tokenizer = tokenizer

    @property
    def token(self):
        t = self._tokenizer.get_token()
        return t if t else Token()

    def next_token(self):
        self._tokenizer.next_token()

    def parse_expr(self, priority = 0):
        if priority < max_priority:
            result = self.parse_expr(priority + 1)
        else:
            result = self.parse_factor()
        while self.token.type in operators[priority]:
            op = self.token
            self.next_token()
            if priority < max_priority:
                result = SynBinaryOp(result, op, self.parse_expr(priority + 1))
            else:
                result = SynBinaryOp(result, op, self.parse_factor())
        return result

    def parse_factor(self):
        filepos = self._tokenizer.curfilepos
        if filepos == None: exit()

        if self.token.type == tt_lparen:
            self.next_token()
            result = self.parse_expr()
            if self.token.type != tt_rparen:
                raise_exception(ParMismatchError(filepos))
        elif self.token.type == tt_identifier:
            result = SynVar(self.token)
        elif self.token.type in [tt_integer, tt_float, tt_string_const]:
            result = SynConst(self.token)
        else:
            raise_exception(UnexpectedTokenError(filepos))

        self.next_token()
        return result
