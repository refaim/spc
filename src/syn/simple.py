# -*- coding: utf-8 -*-

'''\
Синтаксический анализатор выражений с объявлениями на псевдоязыке.
Грамматика языка:

    program ::= (declarations)* expressions
    expressions ::= (expression)*
    declarations ::= (declaration)*
    declaration ::= type identifier
    type ::= ("array" | "function" | "record" | "var")
    identifier ::= (letter | "_" ) (letter | digit | "_" )*

Выражения аналогичны выражениям языка Pascal.
Для соответствующих типов допустимы операции взятия индекса, вызова,
выбора поля (для array, function и record соответственно). К результату такой
операции применима любая операция. В выражениях допускаются целые числа,
строковые константы, а также числа с плавающей точкой. '''

from common.functions import copy_args
from common.errors import *
from tok.token import tt
from expressions import ExprParser
from table import SimpleSymTable
from tree import *

class SimpleParser(ExprParser):
    ''' Класс, реализующий разбор объявлений и "сложных" операций
    (взятие индекса, вызов, взятие поля). Разбор арифметических выражений
    осуществляется родительским классом ExprParser в функции parse_expression() '''

    @copy_args
    def __init__(self, tokenizer):
        self.symtable = SimpleSymTable()
        self.in_symbol = False

    def return_factor(self, factor):
        # это такой маленький костыль, перегрузка функции
        need_next = isinstance(factor, SynConst)
        if need_next:
            self.next_token()
        return factor

    def parse_declarations(self):
        ''' Разбор блока объявлений '''
        simple_types = { "array": tt.kwArray, "function": tt.kwFunction,
                         "record": tt.kwRecord, "var": tt.kwVar }
        while self.token.value in simple_types:
            idtype = simple_types[self.token.value]
            self.next_token()
            idname = self.token.value
            if self.token.type == tt.identifier:
                self.symtable[idname] = idtype
            elif idname in simple_types:
                self.e(E_RESERVED_NAME.format(idname))
            else:
                self.e('Identifier expected')
            self.next_token()

    def parse_complex_expr(self, result):
        ''' Разбор "сложных" операций. '''
        def parse_record(opr):
            if self.token.type == tt.identifier:
                res = SynOperation(opr, result, SynVar(self.token))
            else:
                self.e('Identifier expected')
            self.next_token()
            return res

        def parse_array(opr):
            self.in_symbol = False
            res = SynOperation(opr, result, self.parse_expression())
            if self.token.type != tt.rbracket:
                self.e('Brackets mismatch', self.prevpos)
            self.next_token()
            return res

        def parse_func(opr):
            self.in_symbol = False
            func = result
            args = [self.parse_expression()] if self.token.type != tt.rparen else []
            while self.token.type == tt.comma:
                self.next_token()
                args.append(self.parse_expression())
            if args and self.token.type != tt.rparen:
                self.e(E_PAR_MISMATCH, pos=self.prevpos)
            self.next_token()
            return SynCall(func, args)

        start_symbols = {
            tt.dot:      (tt.kwRecord,   parse_record, E_REQUEST_FIELD),
            tt.lparen:   (tt.kwFunction, parse_func,   E_CALL),
            tt.lbracket: (tt.kwArray,    parse_array,  E_SUBSCRIPT),
        }

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
        complex_ops = (tt.dot, tt.lparen, tt.lbracket)
        if self.token.value not in self.symtable:
            self.e(E_UNDECLARED.format(self.token.value))
        result = SynVar(self.token)
        self.next_token()
        if self.token.type in complex_ops:
            return self.parse_complex_expr(result)
        else:
            return result
