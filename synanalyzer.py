# -*- coding: utf-8 -*-

from token import Token, tt, dlm, kw, op
from errors import *
from syn import *

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
        while self.token.type in binary_ops[priority]:
            opr = self.token
            self.next_token()
            if priority < max_priority:
                result = SynBinaryOp(result, opr, self.parse_expr(priority + 1))
            else:
                result = SynBinaryOp(result, opr, self.parse_factor())
                #result = SynUnaryOp(opr, self.parse_factor())
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
        #elif self.token.type in unary_ops:
        #    opr = self.token
        #    self.next_token()
        #    result = SynUnaryOp(opr, self.parse_factor())
        else:
            self.e(UnexpectedTokenError, [self.token.text])

        # это такой маленький костыль
        need_next = (not isinstance(self, SimpleParser) or\
            isinstance(result, SynConst)) #and not isinstance(result, SynUnaryOp)
        if need_next: self.next_token()
        return result

    def parse_identifier(self):
        return SynVar(self.token)

class SimpleParser(ExprParser):
    def parse_decl(self):
        self.symtable = {}
        self.in_symbol = False

        allowed = { "array": kw.array, "function": kw.function,
                         "record": kw.record, "var": kw.var }
        while self.token.value in allowed:
            idtype = allowed[self.token.value]
            self.next_token()
            idname = self.token.value
            if self.token.type == tt.identifier:
                self.symtable[idname] = idtype
            elif idname in allowed:
                self.e(ReservedNameError, [idname])
            else:
                self.e(IdentifierExpError)
            self.next_token()

    def parse_identifier(self):

        def parse_symbol(symtype, opr):

            def parse_record():
                self.in_symbol = True
                return SynBinaryOp(result, opr, self.parse_identifier())

            def parse_array():
                self.in_symbol = False
                res = SynBinaryOp(result, opr, self.parse_expr())
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

        start_symbols = { op.dot: (kw.record, RecordError),
                          dlm.lparen: (kw.function, CallError),
                          dlm.lbracket: (kw.array, SubscriptError) }

        if self.token.type == tt.identifier:
            varname = self.token.value
            if not self.in_symbol and varname not in self.symtable:
                self.e(UndeclaredIdentifierError, [varname])
            result = SynVar(self.token)
            self.next_token()
            if self.token.type in start_symbols:
                symtype, symerror = start_symbols[self.token.type]
                while self.token.type in start_symbols and\
                     (self.in_symbol or self.symtable[varname] == symtype):
                    symtype, symerror = start_symbols[self.token.type]
                    opr = self.token
                    self.next_token()
                    result = parse_symbol(symtype, opr)
                    self.in_symbol = True
                else:
                    if not self.in_symbol: self.e(symerror)
            self.in_symbol = False
            return result
        elif self.in_symbol:
            self.e(IdentifierExpError)
        else:
            return self.parse_expr()
