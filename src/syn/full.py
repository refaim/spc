# -*- coding: utf-8 -*-

from common.functions import *
from common.errors import *
from tok.token import tt, dlm, op, kw
from expressions import ExprParser
from syn import *
from sym import *

class Parser(ExprParser):
    def __init__(self, tokenizer):
        ExprParser.__init__(self, tokenizer)
        self.symtable = SymTable()
        self.anon_types_count = 0

        self.cursymtable = self.symtable
        self.symtablecheck = True

    def e(self, error, params=[], fp=None):
        if error is ExpError:
            tok = self.token
            params.append(tok.value if tok.value else tok.text)
        ExprParser.e(self, error, params, fp)

    def require_token(self, tokentype):
        if self.token.type != tokentype:
            self.e(ExpError, [str(tokentype)])
        self.next_token()

    def parse_identifier(self):
        name = self.token.value
        if name not in self.cursymtable:
            self.e(UndeclaredIdentifierError, [name])
        # temporary
        return SynVar(name)
    
    def parse_decl(self):
        
        def parse_type():
            typename = self.token.value
            #if typename not in self.cursymtable:
            #    self.e(ExpError, ['Identifier'])
            if typename not in self.cursymtable:
                self.e(UnknownTypeError, [typename])
            if not self.cursymtable[typename].istype():
                self.e(ExpError, ['Typename'])
            self.next_token()
            return self.cursymtable[typename]

        def parse_ident():
            name = self.token.value
            self.require_token(tt.identifier)
            if name in kw:
                self.e(ReservedNameError)
            if self.symtablecheck and name in self.cursymtable:
                self.e(RedeclaredIdentifierError, [name])
            return name
        
        def parse_ident_list():
            names = [parse_ident()]
            while self.token.type == dlm.comma:
                self.next_token()
                names.append(parse_ident())
            return names

        def parse_const_decl():
            constname = parse_ident()
            if self.token.type == dlm.colon:
                self.next_token()
                consttype = parse_type()
            else:
                consttype = None
            self.require_token(op.equal)
            constvalue = self.parse_expr()
            if consttype is None:
                consttype = self.get_expr_type(constvalue)
            else:
                self.assert_types(self.get_expr_type(constvalue), consttype)
            self.require_token(dlm.semicolon)
            
            self.cursymtable.insert(
                SymConst(constname, consttype, constvalue))

        def parse_var_decl():
            varnames = parse_ident_list()
            self.require_token(dlm.colon)
            vartype = parse_type()
            if self.token.type == op.equal:
                if len(varnames) > 1:
                    self.e(VarInitError)
                self.next_token()
                varvalue = self.parse_expr()
                self.assert_types(self.get_expr_type(varvalue), vartype)
            else:
                varvalue = None
            self.require_token(dlm.semicolon)

            for var in varnames:
                self.cursymtable.insert(
                    SymVar(var, vartype, varvalue))


        declarations = { kw.const: parse_const_decl,
                         kw.var: parse_var_decl }

        while self.token.type in declarations:
            parsefunc = declarations[self.token.type]
            self.next_token()
            parsefunc()
            while self.token.type == tt.identifier:
                parsefunc()

    def get_expr_type(self, expr):
        return self.cursymtable['integer']

    def assert_types(self, first, second):
        pass

        '''allowed = { tt.integer: SymTypeInt, tt.float: SymTypeFloat }
        go'od_value = self.token.type in allowed
        if good_value:
            cvalue = self.token.value
        else:
            self.e('неправильное значение')
        if ctype is None:
            ctype = allowed[self.token.type]()
        elif not isinstance(ctype, allowed[self.token.type]):
            self.e('несоответствие типа и значения')
        self.symtable.insert(SymConst(cname, ctype, cvalue))'''
