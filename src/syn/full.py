# -*- coding: utf-8 -*-

from common.functions import *
from common.errors import *
from tree import *
from table import *
from tok.token import tt, keywords
from expressions import ExprParser

class Parser(ExprParser):
    def __init__(self, tokenizer):
        super(Parser, self).__init__(tokenizer)
        self.symtable_stack = [SymTable()]
        self.symtable.insert(SymTypeInt())
        self.symtable.insert(SymTypeReal())
        self.statement_stack = []
        self.anonymous_types = 0
        self.clear_position()

    def __iter__(self):
        while self.token.type != tt.eof:
            yield self.parse_statement()

    @property
    def symtable(self): return self.symtable_stack[-1]
    def find_symbol(self, name):
        for table in reversed(self.symtable_stack):
            if name in table:
                return table[name]
        return None

    def e(self, error, params=[], fp=None):
        if self._saved_pos:
            fp = self._saved_pos
            self.clear_position()
        if error in [ExpError, NotAllowedError]:
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

    def anonymous_typename(self):
        name = 'ARecordType' + str(self.anonymous_types)
        self.anonymous_types += 1
        return name

    def parse(self):
        self.parse_declarations()
        self.require_token(tt.kwBegin)
        self.parse_statement()
        self.require_token(tt.kwEnd)
        self.require_token(tt.dot)

    def parse_identifier_name(self):
        name = self.token.value
        self.save_position()
        self.require_token(tt.identifier)
        if name in keywords:
            self.e(ReservedNameError)
        if name in self.symtable:
            self.e(RedeclaredIdentifierError, [name])
        self.clear_position()
        return name

    def parse_indentifier(self):
        return SynVar(self.parse_indentifier_name())

    def parse_declarations(self):

        def parse_type():
            complex = { tt.kwArray: parse_array, tt.kwRecord: parse_record }
            ttype = self.token.type
            if ttype in complex:
                self.next_token()
                return complex[ttype]()
            type = self.find_symbol(self.token.value)
            if type is None:
                self.e(UnknownTypeError, [self.token.value])
            if not type.is_type():
                self.e(ExpError, ['Typename'])
            self.next_token()
            return type

        def parse_array():
            self.require_token(tt.lbracket)
            lbound = self.require_token(tt.integer).value
            self.save_position()
            self.require_token(tt.double_dot)
            rbound = self.require_token(tt.integer).value
            self.require_token(tt.rbracket)
            self.require_token(tt.kwOf)
            atype = parse_type()
            if lbound > rbound:
                self.e(RangeBoundsError)
            self.clear_position()
            return SymTypeArray(atype, SymTypeRange(lbound, rbound))

        def parse_record():
            table = SymTable()
            self.symtable_stack.append(table)
            while self.token.type == tt.identifier:
                parse_var_decl()
            self.require_token(tt.kwEnd)
            return SymTypeRecord(
                self.anonymous_typename(), self.symtable_stack.pop())

        def parse_ident_list():
            names = [self.parse_identifier_name()]
            while self.token.type == tt.comma:
                self.next_token()
                names.append(self.parse_identifier_name())
            return names

        def parse_type_decl():
            typename = self.parse_identifier_name()
            self.require_token(tt.equal)
            ttype = parse_type()
            self.require_token(tt.semicolon)
            if isinstance(ttype, SymTypeAlias):
                ttype = ttype.type
            self.symtable.insert(SymTypeAlias(typename, ttype))

        def parse_const_decl():
            constname = self.parse_identifier_name()
            if self.token.type == tt.colon:
                self.next_token()
                consttype = parse_type()
            else:
                consttype = None
            self.require_token(tt.equal)
            constvalue = self.parse_expression()
            if consttype is None:
                consttype = self.get_expr_type(constvalue)
            else:
                self.assert_types(self.get_expr_type(constvalue), consttype)
            self.require_token(tt.semicolon)
            self.symtable.insert(SymConst(constname, consttype, constvalue))

        def parse_var_decl():
            varnames = parse_ident_list()
            self.require_token(tt.colon)
            vartype = parse_type()
            if self.token.type == tt.equal:
                if len(varnames) > 1:
                    self.e(VarInitError)
                self.next_token()
                varvalue = self.parse_expression()
                self.assert_types(self.get_expr_type(varvalue), vartype)
            else:
                varvalue = None
            self.require_token(tt.semicolon)
            for var in varnames:
                self.symtable.insert(SymVar(var, vartype, varvalue))

        def parse_subprogram(has_result):
            def parse():
    
                def parse_args():
                    while self.token.type in [tt.kwVar, tt.identifier]:
                        by_value = True
                        if self.token.type == tt.kwVar:
                            by_value = False
                            self.next_token()
                        self.require_token(tt.identifier)
                        name = self.parse_identifier_name()
                        self.require_token(tt.colon)
                        type = parse_type()
                        self.require_token(tt.semicolon)
                        self.symtable.insert(
                            SymFunctionArgument(name, type, by_value))

                name = self.parse_identifier_name()
                args = SymTable()
                if self.token.type == tt.lparen:
                    if self.token.type != tt.rparen:
                        self.symtable_stack.append(args)
                        parse_args()
                        self.symtable_stack.pop()
                    self.require_token(tt.rparen)
                if has_result:
                    self.require_token(tt.colon)
                    result_type = parse_type()
                else:
                    result_type = None
                self.require_token(tt.semicolon)
                declarations = SymTable()
                self.symtable_stack.append(declarations)
                parse_declarations()
                body = self.parse_statement()
                self.symtable_stack.pop()
                return SymTypeFunction(name, args, result_type, declarations, body)

            return parse

        declarations = {
            tt.kwType: parse_type_decl,
            tt.kwConst: parse_const_decl,
            tt.kwVar: parse_var_decl,
            tt.kwFunction: parse_subprogram(True),
            tt.kwProcedure: parse_subprogram(False),
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

    def parse_expression(self):
        expression = ExprParser.parse_expression(self)
        if self.token.type == tt.assign:
            assignment = self.token
            self.next_token()
            expression = SynOperation(
                assignment, expression, self.parse_expression())
        #self.require_token(tt.semicolon)
        return expression

    def parse_condition(self):
        pass

    def parse_statement(self):

        def parse_statement_block():
            block = SynStatementBlock()
            while self.token.type != tt.kwEnd:
                statement = self.parse_statement()
                block.add(statement)
            self.next_token()
            return block

        def parse_statement_if():
            condition = self.parse_condition()
            self.require_token(tt.kwThen)
            action = self.parse_statement()
            if self.token.type == tt.kwElse:
                self.next_token()
                other_action = self.parse_statement()
            else:
                other_action = None
            return SynStatementIf(condition, action, other_action)

        def parse_statement_while():
            condition = self.parse_condition()
            self.require_token(tt.kwDo)
            statement = SynStatementWhile(condition, None)
            self.statement_stack.append(statement)
            statement.action = self.parse_statement()
            self.statement_stack.pop()
            return statement

        def parse_statement_for():
            counter = self.parse_identifier()
            self.require_token(tt.asign)
            initial = self.parse_expression()
            self.require_token(tt.kwTo)
            final = self.parse_expression()
            self.require_token(tt.kwDo)
            statement = SynStatementFor(counter, initial, final, None)
            self.statement_stack.append(statement)
            statement.action = self.parse_statement()
            return self.statement_stack.pop()

        def parse_break_or_continue(StatementClass):
            def parse():
                for statement in reversed(self.statement_stack):
                    if statement.is_loop():
                        return StatementClass()
                self.e(NotAllowedError)
            return parse

        handlers = {
            tt.kwBegin: parse_statement_block,
            tt.kwIf: parse_statement_if,
            tt.kwWhile: parse_statement_while,
            tt.kwFor: parse_statement_for,
            tt.kwBreak: parse_break_or_continue(SynStatementBreak),
            tt.kwContinue: parse_break_or_continue(SynStatementContinue),
        }

        if self.token.type in handlers:
            self.next_token()
            statement = handlers[self.token.type]()
            self.require_token(tt.semicolon)
            return statement
        else:
            return self.parse_expression()
