# -*- coding: utf-8 -*-

from common import *
from errors import *
from syn import *
from sym import *
from token import Token, tt, dlm, op, kw

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

    def e(self, error, params = [], fp = None):
        if fp is None: fp = self.token.linepos
        raise_exception(error(fp, params))

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
        return result

    def parse_factor(self):
        if self.token.type == tt.eof:
            return None
        filepos = self.token.linepos

        if self.token.type == dlm.lparen:
            self.next_token()
            result = self.parse_expr()
            if self.token.type != dlm.rparen:
                self.e(ParMismatchError, fp = filepos)
        elif self.token.type == tt.identifier:
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
        need_next = (not isinstance(self, SimpleParser) or \
            isinstance(result, SynConst))# and not isinstance(result, SynUnaryOp)
            #or self.token.type == dlm.rparen
        if need_next:
            self.next_token()
        return result

    def parse_identifier(self):
        return SynVar(self.token)

class SimpleParser(ExprParser):
    def parse_decl(self):
        self.symtable = SimpleSymTable()
        self.in_symbol = False

        simple_types = { "array": kw.array, "function": kw.function,
                         "record": kw.record, "var": kw.var }
        while self.token.value in simple_types:
            idtype = simple_types[self.token.value]
            self.next_token()
            idname = self.token.value
            if self.token.type == tt.identifier:
                self.symtable[idname] = idtype
            elif idname in simple_types:
                self.e(ReservedNameError, [idname])
            else:
                self.e(IdentifierExpError)
            self.next_token()

    def parse_complex_expr(self, result):

        def parse_record(opr):
            if self.token.type == tt.identifier:
                res = SynDotOp(result, opr, SynVar(self.token))
            else:
                self.e(IdentifierExpError)
            self.next_token()
            return res

        def parse_array(opr):
            self.in_symbol = False
            res = SynBinaryOp(result, opr, self.parse_expr())
            if self.token.type != dlm.rbracket:
                self.e(BracketsMismatchError, fp = self.prevpos)
            self.next_token()
            return res

        def parse_func(opr):
            self.in_symbol = False
            func = result
            args = [self.parse_expr()] if self.token.type != dlm.rparen else []
            while self.token.type == dlm.comma:
                self.next_token()
                args.append(self.parse_expr())
            if not empty(args) and self.token.type != dlm.rparen:
                self.e(ParMismatchError, fp = self.prevpos)
            self.next_token()
            return SynFunctionCall(func, args)

        start_symbols = {op.dot: (kw.record, parse_record, RecordError),
                         dlm.lparen: (kw.function, parse_func, CallError),
                         dlm.lbracket: (kw.array, parse_array, SubscriptError)}

        var = str(result)
        if self.token.type in start_symbols:
            symtype, symfunc, symerror = start_symbols[self.token.type]
            while self.token.type in start_symbols and \
                 (self.in_symbol or self.symtable[var] == symtype):
                symtype, symfunc, symerror = start_symbols[self.token.type]
                opr = self.token
                self.next_token()
                result = symfunc(opr)
                self.in_symbol = True
            else:
                if not self.in_symbol: self.e(symerror)
        return result

    def parse_identifier(self):
        complex_ops = (op.dot, dlm.lparen, dlm.lbracket)
        if self.token.value not in self.symtable:
            self.e(UndeclaredIdentifierError, [self.token.value])
        result = SynVar(self.token)
        self.next_token()
        if self.token.type in complex_ops:
            return self.parse_complex_expr(result)
        else:
            return result

class Parser(ExprParser):
    pass
