# -*- coding: utf-8 -*-

from common.functions import copy_args
from common.errors import *
from tok.token import tt
from tree import *

binary_ops = [
    [
        tt.assign,
    ],
    [
        tt.equal,
        tt.not_equal,
        tt.less,
        tt.greater,
        tt.greater_or_equal,
        tt.less_or_equal
    ],
    [
        tt.plus,
        tt.minus,
        tt.logic_or,
        tt.logic_xor,
    ],
    [
        tt.mul,
        tt.div,
        tt.shl,
        tt.shr,
        tt.int_div,
        tt.int_mod,
        tt.logic_and
    ],
    [],
]
max_priority = len(binary_ops) - 1

class ExprParser(object):
    @copy_args
    def __init__(self, tokenizer): pass

    def __iter__(self):
        while self.token.type != tt.eof:
            yield self.parse_expression()

    def e(self, message, pos=None):
        if pos is None:
            pos = self.token.linepos
        raise SynError(message, pos)

    @property
    def token(self):
        return self.tokenizer.get_token()

    def next_token(self):
        self.prevpos = self.token.linepos
        self.tokenizer.next_token()

    def parse_expression(self):
        return self.internal_parse(0)

    def internal_parse(self, priority):
        if priority < max_priority:
            result = self.internal_parse(priority + 1)
        else:
            result = self.parse_factor()
        while self.token.type in binary_ops[priority]:
            operation = self.token
            self.next_token()
            result = SynOperation(
                operation, result, self.internal_parse(priority + 1))
        return result

    def parse_factor(self):
        if self.token.type == tt.eof:
            return None
        position = self.token.linepos

        if self.token.type == tt.lparen:
            self.next_token()
            result = self.parse_expression()
            if self.token.type != tt.rparen:
                self.e('Parenthesis mismatch', position)
        elif self.token.type == tt.identifier:
            result = self.parse_identifier()
        elif self.token.type in (tt.integer, tt.real, tt.string_const):
            result = SynConst(self.token)
        else:
            self.e("Unexpected character '{0}'".format(self.token.text))
        return self.return_factor(result)

    def return_factor(self, factor):
        self.next_token()
        return factor

    def parse_identifier(self):
        return SynVar(self.token)
