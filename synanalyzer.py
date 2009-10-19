# -*- coding: utf-8 -*-

from errors import raise_exception,\
    UnexpectedTokenError, ParMismatchError, DeclarationError
from token import Token, tt, dlm, kw
from syn import *

operators = [[dlm.plus, dlm.minus], [dlm.mul, dlm.div]]
max_priority = len(operators) - 1

class Parser:
    def __init__(self, tokenizer):
        self._tokenizer = tokenizer
        self._symtable = {}
        
    @property
    def token(self):
        t = self._tokenizer.get_token()
        return t if t else Token()

    @property
    def filepos(self):
        return self._tokenizer.curfilepos

    def next_token(self):
        self._tokenizer.next_token()

    def parse_decl(self):
        allowed = { "array": kw.array, "function": kw.function,
                    "record": kw.record, "var": kw.var }
        while self.token.value in allowed:
            itype = allowed[self.token.value]
            self.next_token()
            if self.token.type == tt.identifier:
                self._symtable[self.token.value] = itype
            else:
                raise_exception(DeclarationError(self.filepos))
            self.next_token()
        # тут будет вызов новой функции для парсинга выражений
        print(self._symtable)

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
        filepos = self.filepos
        if filepos == None: exit()

        if self.token.type == dlm.lparen:
            self.next_token()
            result = self.parse_expr()
            if self.token.type != dlm.rparen:
                raise_exception(ParMismatchError(filepos))
        elif self.token.type == tt.identifier:
            result = SynVar(self.token)
        elif self.token.type in [tt.integer, tt.float, tt.string_const]:
            result = SynConst(self.token)
        else:
            raise_exception(UnexpectedTokenError(filepos))

        self.next_token()
        return result
