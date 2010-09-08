# -*- coding: utf-8 -*-

from common.functions import *
from common.errors import *
from tok.token import tt, dlm, op
from tree import *

#unary_ops = [op.minus, op.plus, op.logic_not]
binary_ops = [[op.equal, op.not_equal, op.lesser, op.greater,
               op.greater_or_equal, op.lesser_or_equal],
             [op.plus, op.minus, op.logic_or],
             [op.mul, op.div, op.shl, op.shr, op.int_div, op.int_mod,
              op.logic_and]]
max_priority = len(binary_ops) - 1

class ExprParser(object):
    def __init__(self, tokenizer):
        self._tokenizer = tokenizer

    def __iter__(self):
        while self.token.type != tt.eof:
            yield self.parse_expr()

    @property
    def token(self):
        return self._tokenizer.get_token()

    def next_token(self):
        self.prevpos = self.token.linepos
        self._tokenizer.next_token()

    def e(self, error, params=[], fp=None):
        if fp is None: 
            fp = self.token.linepos
        raise_exception(error(fp, params))

    def parse_expr(self, priority=0):
        if priority < max_priority:
            result = self.parse_expr(priority + 1)
        else:
            result = self.parse_factor()
        while self.token.type in binary_ops[priority]:
            opr = self.token
            self.next_token()
            if priority < max_priority:
                result = SynBinaryOp(result, opr, self.parse_expr(priority + 1))
            else:
                result = SynBinaryOp(result, opr, self.parse_factor())
        return result

    def parse_factor(self):
        if self.token.type == tt.eof:
            return None
        filepos = self.token.linepos

        if self.token.type == dlm.lparen:
            self.next_token()
            result = self.parse_expr()
            if self.token.type != dlm.rparen:
                self.e(ParMismatchError, fp=filepos)
        elif self.token.type == tt.identifier:
            result = self.parse_identifier()
        elif self.token.type in (tt.integer, tt.real, tt.string_const):
            result = SynConst(self.token)
        #elif self.token.type in unary_ops:
        #    opr = self.token
        #    self.next_token()
        #    result = SynUnaryOp(opr, self.parse_factor())
        else:
            self.e(UnexpectedTokenError, [self.token.text])
        return self.return_factor(result)

    def return_factor(self, factor):
        self.next_token()
        return factor

    def parse_identifier(self):
        return SynVar(self.token)
