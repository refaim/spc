# -*- coding: utf-8 -*-

'''\
Синтаксический анализатор выражений с объявлениями на псевдоязыке.
Грамматика языка:

    program ::= declarations | expressions

    declarations ::= declaration*
    declaration ::= type | identifier
    type ::= ("array" | "function" | "record" | "var")
    identifier ::= (letter | "_" ) (letter | digit | "_" )*

    expressions ::= expression*
Выражения аналогичны выражениям языка Pascal.
Для соответствующих типов допустимы операции взятия индекса, вызова,
выбора поля (для array, function и record соответственно). К результату такой
операции применима любая операция. В выражениях допускаются целые числа,
строковые константы, а также числа с плавающей точкой. '''

from common.functions import *
from common.errors import *
from tok.token import tt, kw, op, dlm
from syn import *
from sym import SimpleSymTable
from analyzer import ExprParser

class SimpleParser(ExprParser):
    ''' Класс, реализующий разбор объявлений и "сложных" операций
    (взятие индекса, вызов, взятие поля). Разбор арифметических выражений
    осуществляется родительским классом ExprParser в функции parse_expr() '''

    def __init__(self, tokenizer):
        ExprParser.__init__(self, tokenizer)
        self.symtable = SimpleSymTable()
        self.in_symbol = False

    def return_factor(self, factor):
        # это такой маленький костыль, перегрузка функции
        need_next = isinstance(factor, SynConst)
        if need_next:
            self.next_token()
        return factor

    def parse_decl(self):
        ''' Разбор блока объявлений '''
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
        ''' Разбор "сложных" операций. '''
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
            if nonempty(args) and self.token.type != dlm.rparen:
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
        ''' Виртуальная функция. Вызывается в родительском классе
        при разборе операндов арифметической операции. Перегружена для
        реализации разбора "сложных" операций. '''
        complex_ops = (op.dot, dlm.lparen, dlm.lbracket)
        if self.token.value not in self.symtable:
            self.e(UndeclaredIdentifierError, [self.token.value])
        result = SynVar(self.token)
        self.next_token()
        if self.token.type in complex_ops:
            return self.parse_complex_expr(result)
        else:
            return result
