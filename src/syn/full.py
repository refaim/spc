    # -*- coding: utf-8 -*-

from common.functions import *
from common.errors import *
from tok.token import tt, dlm, op, kw
from expressions import ExprParser
from tree import *
from table import *

class Parser(ExprParser):
    def __init__(self, tokenizer):
        super(Parser, self).__init__(tokenizer)
        self.symtable = SymTable()
        self._saved_pos = None
        #self.anon_types_count = 0
        self.current_scope = self.symtable
        #self.symtablecheck = True

    def e(self, error, params=[], fp=None):
        if self._saved_pos:
            fp = self._saved_pos
            self.clear_position()
        if error is ExpError:
            tok = self.token
            params.append(tok.value if tok.value else tok.text)
        super(Parser, self).e(error, params, fp)

    def save_position(self):
        # save current token position for error messages
        self._saved_pos = self.token.linepos

    def clear_position(self):
        self._saved_pos = None

    def require_token(self, tokentype):
        current = self.token
        if current.type != tokentype:
            if hasattr(tokentype, 'text'):
                reqtype = tokentype.text
            else:
                reqtype = str(tokentype)
            self.e(ExpError, [reqtype])
        self.next_token()
        return current

    def parse_block(self, last=False):
        self.parse_decl()
        self.require_token(kw.begin)
        self.require_token(kw.end)
        self.require_token(op.dot if last else dlm.semicolon)

    def parse_decl(self):
        
        def verify_type_existence(noarrays=False):
            if self.token.type == kw.array:
                if noarrays:
                    self.e(NotYetImplementedError, 
                           ['Constant and nested arrays'])
                return parse_array_desc()
            typename = self.token.value
            if typename not in self.current_scope:
                self.e(UnknownTypeError, [typename])
            if not self.current_scope[typename].istype():
                self.e(ExpError, ['Typename'])
            self.next_token()
            return self.current_scope[typename]

        def parse_ident():
            name = self.token.value
            self.save_position()
            self.require_token(tt.identifier)
            if name in kw:
                self.e(ReservedNameError)
            if name in self.current_scope:
                self.e(RedeclaredIdentifierError, [name])
            self.clear_position()
            return name
        
        def parse_ident_list():
            names = [parse_ident()]
            while self.token.type == dlm.comma:
                self.next_token()
                names.append(parse_ident())
            return names

        def parse_array_desc():
            self.next_token()
            self.require_token(dlm.lbracket)
            lbound = self.require_token(tt.integer).value
            self.save_position()
            self.require_token(dlm.double_dot)
            rbound = self.require_token(tt.integer).value
            self.require_token(dlm.rbracket)
            self.require_token(kw.of)
            atype = verify_type_existence(noarrays=True)
            if lbound > rbound:
                self.e(RangeBoundsError)
            self.clear_position()
            arange = self.current_scope.insert(SymTypeRange(lbound, rbound))
            return self.current_scope.insert(SymTypeArray(atype, arange))

        def parse_type_decl():
            typename = parse_ident()
            self.require_token(op.equal)

            if self.token.type == kw.array:
                arraytype = parse_array_desc()
                self.require_token(dlm.semicolon)
                self.current_scope.insert(SymTypeAlias(typename, arraytype))
                return
            if self.token.type == kw.record:
                pass

            sourcetype = verify_type_existence()
            self.require_token(dlm.semicolon)
            if isinstance(sourcetype, SymTypeAlias):
                sourcename = sourcetype.target
            else:
                sourcename = sourcetype.getname()
            self.current_scope.insert(
                SymTypeAlias(typename, sourcename))

        def parse_const_decl():
            constname = parse_ident()
            if self.token.type == dlm.colon:
                self.next_token()
                consttype = verify_type_existence(noarrays=True)
            else:
                consttype = None
            self.require_token(op.equal)
            constvalue = self.parse_expr()
            if consttype is None:
                consttype = self.get_expr_type(constvalue)
            else:
                self.assert_types(self.get_expr_type(constvalue), consttype)
            self.require_token(dlm.semicolon)
            
            self.current_scope.insert(
                SymConst(constname, consttype, constvalue))

        def parse_var_decl():
            varnames = parse_ident_list()
            self.require_token(dlm.colon)
            vartype = verify_type_existence()
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
                self.current_scope.insert(
                    SymVar(var, vartype, varvalue))

        def parse_func_decl():
            pass

        declarations = { 
            kw.type: parse_type_decl,
            kw.const: parse_const_decl,
            kw.var: parse_var_decl,
            kw.function: parse_func_decl,
        }

        while self.token.type in declarations:
            parsefunc = declarations[self.token.type]
            self.next_token()
            parsefunc()
            while self.token.type == tt.identifier:
                parsefunc()
               
    def get_expr_type(self, expr):
        return SymTypeInt()

    def assert_types(self, first, second):
        pass

