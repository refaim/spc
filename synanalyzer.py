# -*- coding: utf-8 -*-

from common import *
from errors import *
from syn import *
from sym import *
from token import tt, dlm, op, kw

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
        elif self.token.type in [tt.integer, tt.real, tt.string_const]:
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

class Parser(ExprParser):
    def __init__(self, tokenizer):
        ExprParser.__init__(self, tokenizer)
        self.symtable = SymTable()
        self.anon_types_count = 0

    def e(self, error, params = [], fp = None):
        if error is ExpError:
            tok = self.token
            params.append(tok.value if tok.value else tok.text)
        ExprParser.e(self, error, params, fp)

    def require_token(self, ttype):
        if self.token.type != ttype:
            self.e(ExpError, [str(ttype)])

    def generate_name(self):
        ''' Генерация имени для анонимного типа '''
        template = '${0}'
        name = template.format(self.anon_types_count)
        self.anon_types_count += 1
        return name

    def get_declared_types(self):
        ''' Получение списка объявленных неанонимных типов '''
        good = lambda t: t.is_type() and first(t.get_name()) != '$'
        return (stype for stype in self.symtable.values() if good(stype))

    def parse_decl(self):
        ''' Разбор всего блока объявлений '''
        # var может встретиться всего один раз
        while self.token.type == kw.var:
            self.next_token()
            varnames = self.parse_vars()
            self.require_token(dlm.colon)
            vartype = self.parse_type()
            self.require_token(dlm.semicolon)
            for var in varnames:
                self.symtable.insert(SymVar(var, vartype))
            self.next_token()

    def parse_vars(self, symtable = None):
        ''' Разбор одной последовательности имен
        в списке объявляемых переменных '''
        # разобраться с кучей проверок, аналогичных следующей строке
        if symtable is None: symtable = self.symtable
        names = [self.parse_identifier(symtable)]
        while self.token.type == dlm.comma:
            self.next_token()
            names.append(self.parse_identifier(symtable))
        return names

    def parse_identifier(self, symtable = None):
        if symtable is None: symtable = self.symtable
        self.require_token(tt.identifier)
        varname = self.token.value
        if varname in kw:
            self.e(ReservedNameError)
        if varname in symtable:
            self.e(RedeclaredIdentifierError, [varname])
        self.next_token()
        return varname

    def parse_type(self, symtable = None):
        ''' Разбор типа объявляемой переменной '''

        def parse_record():
            record = SymTypeRecord(self.generate_name(),
                                   self.get_declared_types())
            self.next_token()
            # нехорошо проверять на EOF, надо починить
            while self.token.type not in (kw.end, tt.eof):
                # см. parse_decl -- повторяющийся код
                varnames = self.parse_vars(record.symtable)
                self.require_token(dlm.colon)
                vartype = self.parse_type(record.symtable)
                # кончился повторяющийся код
                if self.token.type != kw.end:
                    self.require_token(dlm.semicolon)
                    self.next_token()
                # и опять повторяем
                for var in varnames:
                    record.symtable.insert(SymVar(var, vartype))
            if self.token.type == kw.end:
                self.next_token()
                self.require_token(dlm.semicolon)
            else:
                self.symtable.insert(record)
            return record

        if symtable is None: symtable = self.symtable
        self.next_token()
        if self.token.type == kw.record:
            return parse_record()

        # заглушка
        if self.token.type not in (tt.identifier, kw.integer, kw.real):
            self.e(ExpError, ['Identifier'])
        typename = self.token.value

        if typename not in symtable:
            self.e(UnknownTypeError, [typename])
        if not symtable[typename].is_type():
            # переделать
            self.e(ExpError, ['Typename'])
        self.next_token()
        return symtable[typename]
