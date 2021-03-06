# -*- coding: utf-8 -*-

import copy

from common.errors import *
from tok.token import tt, keywords
from tree import *
from table import *
from expressions import ExprParser

class Parser(ExprParser):
    def __init__(self, tokenizer):
        super(Parser, self).__init__(tokenizer)
        self.end_of_program = False
        self.allow_empty = False
        self.symtable_stack = SymTableStack(SymTable())
        self.symtable.insert(SymTypeInt())
        self.symtable.insert(SymTypeReal())
        self.block_depth = 0
        self.loop_depth = 0
        self.anonymous_types = 0
        self.current_function = None
        self.look_up = False
        self.clear_position()

    @property
    def symtable(self): return self.symtable_stack.current_table
    def find_symbol(self, name): return self.symtable_stack.find(name)

    def get_root_type(self, type_):
        while type_ and (not type_.is_type() or isinstance(type_, SymTypeAlias)):
            type_ = type_.type
        return type_

    def get_type(self, stmt):
        if isinstance(stmt, Symbol):
            return self.get_root_type(stmt)
        type_ = stmt.type_(self.symtable_stack)
        return self.get_root_type(type_)

    def expect(self, expected):
        found = self.token.value or self.token.text
        self.e(E_EXPECTED, expected, found)

    def e(self, message, *args):
        if self._saved_pos:
            pos = self._saved_pos
            self.clear_position()
        else:
            pos = self.token.linepos
        raise SynError(message, pos, *args)

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
            self.expect(reqtype)
        self.next_token()
        return current

    def anonymous_typename(self):
        name = 'ARecordType' + str(self.anonymous_types)
        self.anonymous_types += 1
        return name

    def parse(self):
        self.parse_declarations()
        if self.token.type == tt.eof:
            self.expect(tt.kwBegin.text)
        return self.parse_statement()

    def parse_declarations(self):

        def parse_type(complex=True):
            complex_handlers = {
                tt.kwArray: parse_array,
                tt.kwRecord: parse_record,
            }
            ttype = self.token.type
            if ttype in complex_handlers:
                if complex:
                    self.next_token()
                    return complex_handlers[ttype]()
                else:
                    self.e('Inline arrays and records are not allowed here')
            type = self.find_symbol(self.token.value)
            if type is None:
                self.e("Unknown type '{0}'", self.token.value)
            if not type.is_type():
                self.expect('Typename')
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
                self.e('Upper bound of range is less than lower bound')
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
                self.e(E_RESERVED_NAME)
            if self.look_up:
                search = self.find_symbol
            else:
                search = lambda name: name in self.symtable
            if search(name):
                self.e(E_REDECLARED, name)
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
                consttype = SymTypeInt() # dummy type
            self.require_token(tt.equal)
            constvalue = self.parse_expression()
            self.require_token(tt.semicolon)
            self.symtable.insert(SymConst(constname, consttype, constvalue))

        def parse_var_decl():
            varnames = parse_ident_list()
            self.require_token(tt.colon)
            vartype = parse_type()
            if self.token.type == tt.equal:
                if len(varnames) > 1:
                    self.e('Only one variable can be initialized')
                self.next_token()
                varvalue = self.parse_expression()
            else:
                varvalue = None
            self.require_token(tt.semicolon)
            for var in varnames:
                self.symtable.insert(SymVar(var, vartype, varvalue))

        def parse_subprogram(has_result):
            def parse():

                def parse_args(current_offset):
                    while self.token.type in (tt.kwVar, tt.identifier):
                        if self.token.type == tt.kwVar:
                            by_value = False
                            self.next_token()
                        else:
                            by_value = True
                        names = parse_ident_list()
                        self.require_token(tt.colon)
                        type = parse_type(complex=False)
                        for name in names:
                            self.symtable.append(
                                SymFunctionArgument(
                                    name, type, by_value, current_offset))
                            current_offset += 4
                        if self.token.type == tt.semicolon:
                            self.next_token()
                            if self.token.type == tt.rparen:
                                self.expect('parameter')

                name = parse_ident()
                function = SymTypeFunction(name)
                self.symtable.insert(function)
                function.args = []
                self.symtable_stack.append(function.args)
                current_offset = 0
                if self.token.type == tt.lparen:
                    self.next_token()
                    if self.token.type != tt.rparen:
                        parse_args(current_offset)
                    self.require_token(tt.rparen)
                if has_result:
                    self.require_token(tt.colon)
                    function.type = parse_type(complex=False)
                else:
                    function.type = None
                function.has_result = has_result
                self.require_token(tt.semicolon)
                function.declarations = SymTable()
                self.symtable_stack.append(function.declarations)
                self.look_up = True
                self.parse_declarations()
                self.look_up = False
                self.block_depth += 1
                self.current_function = function
                function.body = self.parse_statement_block()
                self.current_function = None
                self.block_depth -= 1
                self.require_token(tt.semicolon)
                self.symtable_stack.pop()
                self.symtable_stack.pop()
                function.table = dict(function.declarations)
                for name in function.table:
                    setattr(function.table[name], 'local', True)
                function.table.update(dict((s.name, s) for s in function.args))

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

    def expr_type(self, expr):
        int_ops = (
            tt.logic_and, tt.logic_or,
            tt.logic_xor, tt.logic_not,
            tt.shr, tt.shl,
            tt.int_div, tt.int_mod,
        )
        comparisons = (
            tt.equal, tt.not_equal,
            tt.less, tt.less_or_equal,
            tt.greater, tt.greater_or_equal,
        )

        if isinstance(expr, SynCall):
            func = self.get_type(expr)
            if func.has_result:
                return func.type
            return None
        if not isinstance(expr, SynOperation):
            return self.get_type(expr)
        optype = expr.operation.type
        if optype == tt.assign:
           raise SynError('Illegal expression', expr.pos)

        for op in expr.operands:
            if isinstance(op, SynCall):
                func = self.get_type(op)
                if not func.has_result:
                    raise SynError(
                        'Procedures are not allowed in expressions',
                        op.caller.pos)

        types = map(self.expr_type, expr.operands)
        ltype = types[0]
        if len(types) == 1:
            if (not isinstance(ltype, SymTypeInt) and
                optype == tt.logic_not
            ):
                raise SynError(E_ORDINAL_EXPECTED, expr.pos)
            return ltype
        else:
            rtype = types[1]
            if (optype != tt.div and
                isinstance(ltype, SymTypeInt) and
                isinstance(rtype, SymTypeInt)
            ):
                return self.find_symbol('integer')
            if optype in int_ops:
                raise SynError(E_INCOMPATIBLE_TYPES, expr.pos, ltype, rtype)
            self.cast_to_real(expr, ltype, rtype)
            if optype == tt.div:
                self.cast_to_real(expr, *map(self.expr_type, expr.operands))
            if optype in comparisons:
                return self.find_symbol('integer')
            else:
                return self.find_symbol('real')

    def cast_to_real(self, expr, ltype, rtype):
        if isinstance(ltype, SymTypeInt):
            expr.operands[0] = SynCastToReal(expr.operands[0])
        elif isinstance(rtype, SymTypeInt):
            expr.operands[1] = SynCastToReal(expr.operands[1])

    def check_program(self, program):
        self.check_types(program)
        table = (func for name, func in self.symtable.iteritems()
                 if isinstance(func, SymTypeFunction))
        for func in table:
            self.symtable_stack.append(func.table)
            self.check_types(func.body)
            self.symtable_stack.pop()

    def check_types(self, stmt):

        def require_ordinal(*expressions):
            for expr in expressions:
                if isinstance(expr, SynOperation):
                    type_ = self.expr_type(expr)
                else:
                    type_ = self.get_type(expr)
                if not isinstance(type_, SymTypeInt):
                    raise SynError(E_ORDINAL_EXPECTED, expr.pos)

        def require_mutable(*expressions):
            for expr in expressions:
                if (isinstance(expr, SynConst) or
                    not isinstance(expr,
                       (SynVar, SynSubscript, SynFieldRequest))
                ):
                    raise SynError('Mutable expression expected', expr.pos)

        def require_statement(expr):
            is_statement = isinstance(expr,
                (SynCall, SynEmptyStatement, \
                 SynStatementBreak, SynStatementContinue))
            is_assignment = isinstance(expr, SynOperation) and \
                 expr.operation.type == tt.assign

            if is_assignment:
                require_mutable(expr.operands[0])

                ltype, rtype = map(self.expr_type, expr.operands)
                if ltype is not rtype:
                    if isinstance(ltype, SymTypeReal):
                        self.cast_to_real(expr, ltype, rtype)
                    else:
                        raise SynError(
                            E_INCOMPATIBLE_TYPES, expr.pos, ltype, rtype)

            elif isinstance(expr, SynCall):
                function = self.find_symbol(expr.caller.name)
                formal = [(arg.type, arg)
                    for i, arg in enumerate(function.args)]
                actual = [(self.expr_type(arg), i)
                    for i, arg in enumerate(expr.args)]
                for (frm_type, frm), (act_type, act_index) in zip(formal, actual):
                    if not frm.by_value:
                        require_mutable(expr.args[act_index])

                    if (isinstance(frm_type, SymTypeReal) and
                        isinstance(act_type, SymTypeInt)
                    ):
                        expr.args[act_index] = SynCastToReal(expr.args[act_index])

                    elif self.get_root_type(frm_type) != self.get_root_type(act_type):
                        raise SynError(E_INCOMPATIBLE_TYPES,
                            expr.args[act_index].pos, frm_type, act_type)

            elif not is_statement:
                raise SynError('Illegal expression', expr.pos)

        def check_for():
            require_ordinal(stmt.counter, stmt.initial, stmt.final)
            require_mutable(stmt.counter)
            self.check_types(stmt.action)

        def check_while_repeat():
            require_ordinal(stmt.condition)
            self.check_types(stmt.action)

        def check_if():
            require_ordinal(stmt.condition)
            self.check_types(stmt.action)
            if stmt.else_action:
                self.check_types(stmt.else_action)

        def check_write():
            for expr in stmt.args:
                self.expr_type(expr)

        def check_result():
            pass

        def check_block():
            for statement in stmt.statements:
                self.check_types(statement)

        handlers = {
            SynStatementBlock: check_block,
            SynStatementFor: check_for,
            SynStatementWhile: check_while_repeat,
            SynStatementRepeat: check_while_repeat,
            SynStatementIf: check_if,
            SynStatementWrite: check_write,
            SynStatementResult: check_result,
        }

        if type(stmt) in handlers:
            handlers[type(stmt)]()
        else:
            require_statement(stmt)

    def parse_identifier(self): # virtual function
        var, name = self.token, self.token.value
        if self.token.type != tt.identifier:
            self.expect(tt.identifier)
        if not self.find_symbol(name):
            self.e(E_UNDECLARED, name)
        return SynVar(var)

    def parse_expression(self, expected='expression'): # virtual function
        if self.token.value in keywords:
            self.expect(expected)
        return ExprParser.parse_expression(self)

    def parse_factor(self): # virtual function

        def parse_call(result):
            function = self.get_type(result)
            params = []
            if not isinstance(function, SymTypeFunction):
                self.e(E_CALL)
            self.next_token()
            if self.token.type != tt.rparen:
                params.append(self.parse_expression())
                while self.token.type == tt.comma:
                    self.next_token()
                    params.append(self.parse_expression())
                if self.token.type != tt.rparen:
                    self.expect(tt.rparen.text)
            if len(params) > len(function.args):
                self.e('Too many actual parameters')
            if len(params) < len(function.args):
                self.e('Not enough actual parameters')
            return SynCall(result, params)

        def parse_field_request(result):
            record = self.get_type(result)
            if not isinstance(record, SymTypeRecord):
                self.e(E_REQUEST_FIELD)
            self.next_token()
            self.symtable_stack.append(record.symtable)
            result = SynFieldRequest(result, self.parse_identifier())
            self.symtable_stack.pop()
            return result

        def parse_subscript(result):
            array = self.get_type(result)
            if not isinstance(array, SymTypeArray):
                self.e(E_SUBSCRIPT)
            self.next_token()
            index = self.parse_expression()
            if self.token.type != tt.rbracket:
                self.expect(tt.rbracket.text)
            return SynSubscript(result, index)

        handlers = {
            tt.lparen: parse_call,
            tt.dot: parse_field_request,
            tt.lbracket: parse_subscript,
        }
        unary_ops = (tt.minus, tt.logic_not)

        op = self.token
        if op.type in unary_ops:
            self.next_token()
            result = SynOperation(op, self.parse_factor())
        else:
            result = ExprParser.parse_factor(self)
        while self.token.type in handlers:
            result = handlers[self.token.type](result)
            self.next_token()
        return result

    def parse_condition(self):
        condition = self.parse_expression()
        return condition

    def parse_statement_block(self):
        self.next_token()
        # prevent memory optimization
        block = copy.deepcopy(SynStatementBlock())
        while self.token.type == tt.semicolon:
            if self.allow_empty:
                block.add(SynEmptyStatement())
                self.allow_empty = False
            self.next_token()
        while not self.end_of_program and self.token.type != tt.kwEnd:
            if self.token.type == tt.eof:
                self.e('Unexpected end of file')
            statement = self.parse_statement()
            block.add(statement)
            if self.token.type != tt.kwEnd:
                self.require_token(tt.semicolon)
            while self.token.type == tt.semicolon:
                self.next_token()
        self.next_token()
        return block

    def parse_statement(self):

        def parse_action():
            self.allow_empty = True
            action = self.parse_statement()
            self.allow_empty = False
            return action

        def parse_loop_action():
            self.loop_depth += 1
            action = parse_action()
            self.loop_depth -= 1
            return action

        def parse_statement_if():
            self.next_token()
            condition = self.parse_condition()
            self.require_token(tt.kwThen)
            action = parse_action()
            if self.token.type == tt.kwElse:
                self.next_token()
                else_action = parse_action()
            else:
                else_action = None
            return SynStatementIf(condition, action, else_action)

        def parse_statement_while():
            self.next_token()
            condition = self.parse_condition()
            self.require_token(tt.kwDo)
            action = parse_loop_action()
            return SynStatementWhile(condition, action)

        def parse_statement_repeat():
            self.next_token()
            action = parse_loop_action()
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
            action = parse_loop_action()
            return SynStatementFor(counter, initial, final, action)

        def parse_break_or_continue(StatementClass):
            def parse():
                if self.loop_depth:
                    self.next_token()
                    return StatementClass()
                self.e(E_NOT_ALLOWED, self.token.value)
            return parse

        def parse_write(newline):
            self.next_token()
            self.require_token(tt.lparen)
            messages = [self.parse_expression()]
            while self.token.type == tt.comma:
                self.next_token()
                messages.append(self.parse_expression())
            self.require_token(tt.rparen)
            return SynStatementWrite(newline, *messages)

        def parse_statement_result():
            if (not self.current_function or
                not self.current_function.has_result
            ):
                self.e(E_NOT_ALLOWED, self.token.value)
            self.next_token()
            self.require_token(tt.assign)
            return SynStatementResult(
                self.parse_expression(), self.current_function.type)

        handlers = {
            tt.kwIf: parse_statement_if,
            tt.kwWhile: parse_statement_while,
            tt.kwRepeat: parse_statement_repeat,
            tt.kwFor: parse_statement_for,
            tt.kwBreak: parse_break_or_continue(SynStatementBreak),
            tt.kwContinue: parse_break_or_continue(SynStatementContinue),
            tt.kwWrite: lambda: parse_write(False),
            tt.kwWriteln: lambda: parse_write(True),
            tt.kwResult: parse_statement_result,
        }

        key = self.token.type
        if key == tt.kwBegin:
            self.block_depth += 1
            statement = self.parse_statement_block()
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
                        self.e(E_NOT_ALLOWED, self.token.value)
            self.block_depth -= 1
        elif key in handlers:
            statement = handlers[key]()
        elif self.block_depth:
            if self.token.type == tt.semicolon:
                statement = SynEmptyStatement()
            else:
                statement = self.parse_expression(expected='statement')
        else:
            self.expect(tt.kwBegin.text)
        return statement
