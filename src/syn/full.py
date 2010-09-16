# -*- coding: utf-8 -*-

import copy

from common.functions import *
from common.errors import *
from tree import *
from table import *
from tok.token import tt, keywords
from expressions import ExprParser

class Parser(ExprParser):
    def __init__(self, tokenizer):
        super(Parser, self).__init__(tokenizer)
        self.end_of_program = False
        self.allow_empty = False
        self.symtable_stack = [SymTable()]
        self.symtable.insert(SymTypeInt())
        self.symtable.insert(SymTypeReal())
        self.block_depth = 0
        self.loop_depth = 0
        self.anonymous_types = 0
        self.clear_position()

    @property
    def symtable(self): return self.symtable_stack[-1]
    def find_symbol(self, name):
        for table in reversed(self.symtable_stack):
            if name in table:
                return table[name]
        return None

    def e(self, error, params=[], pos=None):
        if self._saved_pos:
            pos = self._saved_pos
            self.clear_position()
        if error is ExpError:
            tok = self.token
            params.append(tok.value if tok.value else tok.text)
        if error is NotAllowedError:
            params = [self.token.value]
        super(Parser, self).e(error, params, pos)

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
        if self.token.type == tt.eof:
            self.e(ExpError, [tt.kwBegin.text])
        return self.parse_statement()

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

        def parse_ident():
            name = self.token.value
            self.save_position()
            self.require_token(tt.identifier)
            if name in keywords:
                self.e(ReservedNameError)
            if name in self.symtable:
                self.e(RedeclaredIdentifierError, [name])
            self.clear_position()
            return name

        def parse_ident_list():
            names = [parse_ident()]
            while self.token.type == tt.comma:
                self.next_token()
                names.append(parse_ident())
            return names

        def parse_type_decl():
            typename = parse_ident()
            self.require_token(tt.equal)
            ttype = parse_type()
            self.require_token(tt.semicolon)
            if isinstance(ttype, SymTypeAlias):
                ttype = ttype.type
            self.symtable.insert(SymTypeAlias(typename, ttype))

        def parse_const_decl():
            constname = parse_ident()
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
                        if self.token.type == tt.kwVar:
                            by_value = False
                            self.next_token()
                        else:
                            by_value = True
                        self.require_token(tt.identifier)
                        name = parse_ident()
                        self.require_token(tt.colon)
                        type = parse_type()
                        self.require_token(tt.semicolon)
                        self.symtable.insert(
                            SymFunctionArgument(name, type, by_value))

                name = parse_ident()
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
                self.parse_declarations()
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

    def parse_identifier(self): # virtual function
        var, name = self.token, self.token.value
        if self.token.type != tt.identifier:
            self.e(ExpError, [tt.identifier])
        if not self.find_symbol(name):
            self.e(UndeclaredIdentifierError, [name])
        return SynVar(var)

    def parse_expression(self, expected='expression'): # virtual function
        if self.token.value in keywords:
            self.e(ExpError, [expected])
        return ExprParser.parse_expression(self)

    def parse_factor(self): # virtual function

        def parse_call():
            pass
        def parse_field_request():
            pass
        def parse_subscript():
            pass
        
        handlers = {
            tt.lparen: parse_call,
            tt.dot: parse_field_request,
            tt.lbracket: parse_subscript,
        }

        result = ExprParser.parse_factor(self)
        if self.token.type in handlers:
            result = handlers[self.token.type]()
        return result

    def parse_condition(self):
        condition = self.parse_expression()
        # todo: check type
        return condition

    def parse_statement(self):

        def parse_statement_block():
            self.allow_empty = True
            self.next_token()
            # prevent memory optimization
            block = copy.deepcopy(SynStatementBlock())
            self.block_depth += 1
            while self.token.type == tt.semicolon:
                if self.allow_empty:
                    block.add(SynEmptyStatement())
                    self.allow_empty = False
                self.next_token()
            while not self.end_of_program and self.token.type != tt.kwEnd:
                if self.token.type == tt.eof:
                    self.e(UnexpectedEOFError)
                statement = self.parse_statement()
                block.add(statement)
                if self.token.type != tt.kwEnd:
                    self.require_token(tt.semicolon)
                while self.token.type == tt.semicolon:
                    self.next_token()
            self.next_token()
            if self.token.type not in (tt.kwElse, tt.kwEnd):
                if self.token.type == tt.dot and self.block_depth > 1:
                    self.require_token(tt.semicolon)
                if self.token.type in (tt.dot, tt.eof) or self.block_depth == 1:
                    self.require_token(tt.dot)
                    self.end_of_program = True
                if self.token.type == tt.semicolon:
                    self.next_token()
                    if self.token.type == tt.kwElse:
                        # todo: fix error message
                        self.e(NotAllowedError)
            self.block_depth -= 1
            return block

        def parse_statement_if():
            self.next_token()
            condition = self.parse_condition()
            self.require_token(tt.kwThen)
            action = self.parse_statement()
            if self.token.type == tt.kwElse:
                self.next_token()
                else_action = self.parse_statement()
            else:
                else_action = None
            return SynStatementIf(condition, action, else_action)

        def parse_statement_while():
            self.next_token()
            condition = self.parse_condition()
            self.require_token(tt.kwDo)
            self.loop_depth += 1
            action = self.parse_statement()
            self.loop_depth -= 1
            return SynStatementWhile(condition, action)

        def parse_statement_repeat():
            self.next_token()
            self.loop_depth += 1
            action = self.parse_statement()
            self.loop_depth -= 1
            self.require_token(tt.kwUntil)
            condition = self.parse_condition()
            return SynStatementRepeat(condition, action)

        def parse_statement_for():
            self.next_token()
            counter = self.parse_identifier()
            self.next_token()
            self.require_token(tt.assign)
            initial = self.parse_expression()
            self.require_token(tt.kwTo)
            final = self.parse_expression()
            self.require_token(tt.kwDo)
            self.loop_depth += 1
            action = self.parse_statement()
            self.loop_depth -= 1
            return SynStatementFor(counter, initial, final, action)

        def parse_break_or_continue(StatementClass):
            def parse():
                if self.loop_depth:
                    self.next_token()
                    return StatementClass()
                self.e(NotAllowedError)
            return parse

        handlers = {
            tt.kwBegin: parse_statement_block,
            tt.kwIf: parse_statement_if,
            tt.kwWhile: parse_statement_while,
            tt.kwRepeat: parse_statement_repeat,
            tt.kwFor: parse_statement_for,
            tt.kwBreak: parse_break_or_continue(SynStatementBreak),
            tt.kwContinue: parse_break_or_continue(SynStatementContinue),
        }

        key = self.token.type
        if key in handlers:
            statement = handlers[key]()
        elif self.block_depth:
            if self.token.type == tt.semicolon:
                statement = SynEmptyStatement()
            else:
                statement = self.parse_expression(expected='statement')
        else:
            self.e(ExpError, [tt.kwBegin.text])
        return statement
