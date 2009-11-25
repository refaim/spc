# -*- coding: utf-8 -*-

from token import Token, tt, dlm, kw
from errors import *
from syn import *

operators = [[dlm.plus, dlm.minus], [dlm.mul, dlm.div]]
max_priority = len(operators) - 1

class BasicParser(object):
    def __init__(self, tokenizer):
        self._tokenizer = tokenizer

    @property
    def token(self):
        t = self._tokenizer.get_token()
        return t if t else Token()

    def e(self, error, params = [], fp = None):
        if fp == None: fp = self.token.linepos
        raise_exception(error(fp, params))

    def next_token(self):
        self.prevpos = self.token.linepos
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
        if self.token.type == None: return None
        filepos = self.token.linepos

        if self.token.type == dlm.lparen:
            self.next_token()
            result = self.parse_expr()
            if self.token.type != dlm.rparen:
                self.e(ParMismatchError, fp = filepos)
        elif self.token.type == tt.identifier or self.token.type in kw:
            result = self.parse_identifier()
        elif self.token.type in [tt.integer, tt.float, tt.string_const]:
            result = SynConst(self.token)
        else:
            self.e(UnexpectedTokenError, [self.token.text])

        # это такой маленький костыль
        if isinstance(self, PseudoLangParser) and\
           not isinstance(result, SynConst):
            self._tokenizer.push_token_back()

        self.next_token()
        return result

    def parse_identifier(self):
        return SynVar(self.token)

class PseudoLangParser(BasicParser):
    @property
    def symtable(self):
        return self._symtable

    def parse_decl(self):
        self._symtable = {}
        self.in_symbol = False

        allowed = { "array": kw.array, "function": kw.function,
                    "record": kw.record, "var": kw.var }
        while self.token.value in allowed:
            idtype = allowed[self.token.value]
            self.next_token()
            idname = self.token.value
            if self.token.type == tt.identifier:
                self._symtable[idname] = idtype
            elif idname in allowed:
                self.e(ReservedNameError, [idname])
            else:
                self.e(IdentifierExpError)
            self.next_token()

    def parse_identifier(self):

        def parse_symbol(symtype, op):

            def parse_record():
                self.in_symbol = True
                return SynBinaryOp(result, op, self.parse_identifier())

            def parse_array():
                self.in_symbol = False
                res = SynBinaryOp(result, op, self.parse_expr())
                if self.token.type != dlm.rbracket:
                    self.e(BracketsMismatchError, fp = self.prevpos)
                self.next_token()
                return res

            def parse_function():
                self.in_symbol = False
                func = result
                args = [self.parse_expr()] if self.token.type != dlm.rparen else []
                while self.token.type == dlm.comma:
                    self.next_token()
                    args.append(self.parse_expr())
                if len(args) and self.token.type != dlm.rparen:
                    self.e(ParMismatchError, fp = self.prevpos)
                self.next_token()
                return SynFunctionCall(func, args)

            symtypes = { kw.record: parse_record, kw.array: parse_array,
                         kw.function: parse_function }
            return symtypes[symtype]()

        start_symbols = { dlm.dot: (kw.record, RecordError),
                          dlm.lparen: (kw.function, CallError),
                          dlm.lbracket: (kw.array, SubscriptError) }

        if self.token.type == tt.identifier:
            varname = self.token.value
            if not self.in_symbol and varname not in self._symtable:
                self.e(UndeclaredIdentifierError, [varname])
            result = SynVar(self.token)
            self.next_token()
            if self.token.type in start_symbols:
                symtype, symerror = start_symbols[self.token.type]
                while self.token.type in start_symbols and\
                     (self.in_symbol or self._symtable[varname] == symtype):
                    symtype, symerror = start_symbols[self.token.type]
                    op = self.token
                    self.next_token()
                    result = parse_symbol(symtype, op)
                    self.in_symbol = True
                else:
                    if not self.in_symbol: self.e(symerror)
            self.in_symbol = False
            return result
        elif self.in_symbol:
            self.e(IdentifierExpError)
        else:
            return self.parse_expr()
