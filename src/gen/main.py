# -*- coding: utf-8 -*-

import sys
import os
import StringIO
import functools

from common.errors import GenError
from common.functions import copy_args
from tok.token import tt
from syn.tree import *
from syn.table import *
import asm


FASM_PATH = os.path.abspath(os.path.join(sys.path[0], '../asm/'))
if not os.path.exists(FASM_PATH):
    raise GenError('FASM include files not found')

def is_windows():
    return 'win' in sys.platform

if '64' in sys.platform:
    raise GenError('64-bit platforms are not supported')

if is_windows():
    HEADER = open(
        os.path.join(FASM_PATH, 'win32header.asm')).read().format(
            os.path.join(FASM_PATH, 'win32include\win32a.inc'))
else:
    HEADER = open(os.path.join(FASM_PATH, 'nix32header.asm')).read()


class Generator(object):
    @copy_args
    def __init__(self, program, parser):
        self.instructions = []
        self.declarations = []
        self.loops = []
        self.string_consts = {}
        self.symtable_stack = [self.parser.symtable]
        self.output = StringIO.StringIO()
        self.label_count = 0

    def find_symbol(self, name):
        for table in reversed(self.symtable_stack):
            if name in table:
                return table[name]

    def get_type(self, *expressions):
        return map(self.parser.expr_type, *expressions)

    def dword(self, arg, offset=0):
        return asm.SizeCast('dword', asm.Offset(arg, offset))

    def stack(self, offset=0):
        return self.dword('esp', offset)

    def allocate(self, name, size, dup=True):
        self.declarations.append(asm.Declaration(name, size, dup))

    def allocate_string(self, string_):
        if string_ in self.string_consts:
            name = self.string_consts[string_]
        else:
            name = 'S' + str(len(self.string_consts))
            self.string_consts[string_] = name
            self.allocate(name, string_, dup=False)
        return name

    def get_labels(self, count=1):
        result = []
        for i in range(count):
            result.append('L' + str(self.label_count))
            self.label_count += 1
        return result[0] if len(result) == 1 else result

    def generate_label(self, name):
        self.instructions.append(asm.Label(name))

    def cmd(self, *commands):
        add_tuple = lambda c:self.instructions.append(
            asm.Command(c[0], *c[1:]))
        one_command = all(not isinstance(cmd, tuple) for cmd in commands)
        if one_command:
            add_tuple(commands)
            return
        for command in commands:
            if isinstance(command, tuple):
                add_tuple(command)
            else:
                self.instructions.append(asm.Command(command))

    def call(self, name):
        if is_windows():
            return asm.Offset(name)
        else:
            return name

    TYPE2STR = {
        SymTypeInt:    'int',
        SymTypeReal:   'real',
        SymTypeArray:  'arr',
        SymTypeRecord: 'rec',
    }
    def generate_variable_name(self, name, type_):
        return '{0}${1}'.format(self.TYPE2STR[type(type_.type)], name)

    def get_variable_name(self, name):
        return self.find_symbol(name).gen_name

    def generate(self):
        self.output.write(HEADER)

        # avoid bug with iteration over UserDict (Python 2.6.4)
        table = dict(self.parser.symtable)

        # reserve memory for global variables
        for name, type_ in table.iteritems():
            if isinstance(type_, (SymVar, SymConst)):
                gen_name = self.generate_variable_name(name, type_)
                self.allocate(gen_name, type_.size)
                table[name].gen_name = gen_name

        self.generate_label('main')
        self.generate_statement(self.program)

        if is_windows():
            self.cmd('stdcall', asm.Offset('ExitProcess'), 0)
        else:
            self.cmd(
                ('mov', 'eax', 0),
                'ret',
            )

        def write_list(list_):
            for i, row in enumerate(list_):
                self.output.write(str(row) +
                    ('\n' if i < len(list_) - 1 else ''))

        if self.declarations:
            if is_windows():
                self.output.write("section '.data' readable writeable\n\n")
            write_list(self.declarations)
            self.output.write('\n\n')

        if is_windows():
            self.output.write("section '.code' readable executable\n\n")
        write_list(self.instructions)

        self.output.write('\n')
        return self.output.getvalue()

    def generate_statement(self, stmt, lvalue=False):

        def jump_if_zero(label):
            self.cmd(
                ('pop', 'eax'),
                ('test', 'eax', 'eax'),
                ('jz', label),
            )

        def generate_operation():
            if len(stmt.operands) == 2:
                self.generate_binary(stmt)
            else:
                self.generate_unary(stmt)

        def generate_subscript():
            self.generate_statement(stmt.array, lvalue=True)
            array_type = self.parser.expr_type(stmt.array)
            self.generate_statement(stmt.index)
            self.cmd(
                ('pop', 'eax'), # index
                ('sub', 'eax', array_type.range.leftbound),
                ('pop', 'ebx'), # base
                ('imul', 'eax', array_type.type.size),
                ('add', 'ebx', 'eax'),
                ('push', 'ebx' if lvalue else self.dword('ebx')),
            )

        def generate_cast():
            self.generate_statement(stmt.expression)
            self.cmd(
                ('fild', self.stack()),
                ('fstp', self.stack()),
            )

        def generate_write():
            formats = {
                SymTypeInt: '%d',
                SymTypeReal: '%f',
            }

            format_string = ''
            occupied_size = 0
            for arg in reversed(stmt.args):
                self.generate_statement(arg)
                arg_type = type(self.parser.expr_type(arg))
                format_string += formats[arg_type]
                occupied_size += 4

            format_string = "'{0}', {1}".format(
                format_string, '10, 0' if stmt.newline else '0')

            format_string_name = self.allocate_string(format_string)

            if arg_type is SymTypeReal:
                self.cmd(
                    ('fld', self.stack()),
                    ('sub', 'esp', '4'),
                    ('fstp', asm.SizeCast('qword', asm.Offset('esp'))),
                )
                occupied_size += 4

            self.cmd(
                ('push', format_string_name),
                ('call', self.call('printf')),
                ('add', 'esp', occupied_size + 4),
            )

        def generate_variable():
            name = self.get_variable_name(stmt.name)
            if lvalue:
                self.cmd('push', name)
            else:
                self.cmd('push', self.dword(name))

        def generate_while():
            start, end = self.get_labels(2)
            self.loops.append((start, end))
            self.generate_label(start)
            self.generate_statement(stmt.condition)
            jump_if_zero(end)
            self.generate_statement(stmt.action)
            self.cmd('jmp', start)
            self.generate_label(end)
            self.loops.pop()

        def generate_repeat():
            start, check, end = self.get_labels(3)
            self.loops.append((check, end))
            self.generate_label(start)
            self.generate_statement(stmt.action)
            self.generate_label(check)
            self.generate_statement(stmt.condition)
            jump_if_zero(start)
            self.generate_label(end)
            self.loops.pop()

        def generate_for():
            start, inc, end = self.get_labels(3)
            self.loops.append((inc, end))
            self.generate_statement(stmt.assignment)
            self.generate_label(start)
            self.generate_statement(stmt.check)
            jump_if_zero(end)
            self.generate_statement(stmt.action)
            self.generate_label(inc)
            self.cmd(
                ('inc', self.dword(self.get_variable_name(stmt.counter.name))),
                ('jmp', start),
            )
            self.generate_label(end)
            self.loops.pop()

        def generate_if():
            self.generate_statement(stmt.condition)
            else_case, endif = self.get_labels(2)
            jump_if_zero(else_case)
            self.generate_statement(stmt.action)
            self.cmd('jmp', endif)
            self.generate_label(else_case)
            if stmt.else_action:
                self.generate_statement(stmt.else_action)
            self.generate_label(endif)

        def generate_block():
            for statement in stmt.statements:
                self.generate_statement(statement)

        handlers = {
            SynOperation: generate_operation,
            SynSubscript: generate_subscript,
            SynCastToReal: generate_cast,
            SynVar: generate_variable,
            SynConst: lambda: self.cmd('push', stmt.name),
            SynStatementIf: generate_if,
            SynStatementFor: generate_for,
            SynStatementWhile: generate_while,
            SynStatementRepeat: generate_repeat,
            SynStatementBreak: lambda: self.cmd('jmp', self.loops[-1][1]),
            SynStatementContinue: lambda: self.cmd('jmp', self.loops[-1][0]),
            SynStatementBlock: generate_block,
            SynStatementWrite: generate_write,
            SynEmptyStatement: lambda: self.cmd('nop'),
        }
        handlers[type(stmt)]()

    def generate_binary(self, binop):

        def generate_assignment():
            self.cmd('mov', self.dword('eax'), 'ebx')

        def generate_logic_or():
            true, false, end = self.get_labels(3)
            self.cmd(
                ('test', 'eax', 'eax'),
                ('jnz', true),
                ('test', 'ebx', 'ebx'),
                ('jz', false),
            )
            self.generate_label(true)
            self.cmd(
                ('mov', 'eax', 1),
                ('jmp', end),
            )
            self.generate_label(false)
            self.cmd('xor', 'eax', 'eax')
            self.generate_label(end)
            self.cmd('push', 'eax')

        def generate_logic_and():
            false, end = self.get_labels(2)
            self.cmd(
                ('test', 'eax', 'eax'),
                ('jz', false),
                ('test', 'ebx', 'ebx'),
                ('jz', false),
                ('mov', 'eax', 1),
                ('jmp', end),
            )
            self.generate_label(false)
            self.cmd('xor', 'eax', 'eax')
            self.generate_label(end)
            self.cmd('push', 'eax')

        def generate_comparison(setcc):
            self.cmd(
                ('cmp', 'eax', 'ebx'),
                (setcc, 'al'),
                ('movzx', 'eax', 'al'),
                ('push', 'eax'),
            )

        def generate_shift(shift):
            self.cmd(
                ('pop', 'ecx'),
                ('pop', 'eax'),
                (shift, 'eax', 'cl'),
                ('push', 'eax'),
            )

        def integer_binary(function):
            @functools.wraps(function)
            def wraps(**kwargs):
                self.cmd(
                    ('pop', 'ebx'),
                    ('pop', 'eax'),
                )
                return function(**kwargs)
            return wraps

        def generate_float_assignment():
            self.cmd(
                ('pop', 'ebx'),
                ('pop', 'eax'),
            )
            generate_assignment()

        def generate_float_arithmetic(command):
            self.cmd(
                ('fld', self.stack(offset=4)),
                (command, self.stack()),
                ('add', 'esp', 4),
                ('fstp', self.stack()),
            )

        def generate_float_comparison(setcc):
            self.cmd(
                ('xor', 'eax', 'eax'),
                ('fld', self.stack()),
                ('fld', self.dword('esp', offset=4)),
                ('fcomip', 'st0', 'st1'),
                (setcc, 'al'),
                ('add', 'esp', 8),
                ('push', 'eax'),
            )

        integer, real = SymTypeInt, SymTypeReal
        BINARY_HANDLERS = {
            (integer, tt.assign): generate_assignment,

            (integer, tt.plus): lambda: self.cmd(
                ('add', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, tt.minus): lambda: self.cmd(
                ('sub', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, tt.mul): lambda: self.cmd(
                ('imul', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, tt.int_div): lambda: self.cmd(
                ('xor', 'edx', 'edx'),
                ('idiv', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, tt.int_mod): lambda: self.cmd(
                ('xor', 'edx', 'edx'),
                ('idiv', 'ebx'),
                ('push', 'edx'),
            ),
            (integer, tt.div): lambda:
                generate_float_arithmetic('fdiv'),

            (integer, tt.equal):
                lambda: generate_comparison('sete'),
            (integer, tt.not_equal):
                lambda: generate_comparison('setne'),
            (integer, tt.less):
                lambda: generate_comparison('setl'),
            (integer, tt.less_or_equal):
                lambda: generate_comparison('setle'),
            (integer, tt.greater):
                lambda: generate_comparison('setg'),
            (integer, tt.greater_or_equal):
                lambda: generate_comparison('setge'),

            (integer, tt.logic_or): generate_logic_or,
            (integer, tt.logic_and): generate_logic_and,
            (integer, tt.logic_xor): lambda: self.cmd(
                ('xor', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, tt.shr): lambda: generate_shift('shr'),
            (integer, tt.shl): lambda: generate_shift('shl'),

            (real, tt.assign): generate_float_assignment,

            (real, tt.plus): lambda:
                generate_float_arithmetic('fadd'),
            (real, tt.minus): lambda:
                generate_float_arithmetic('fsub'),
            (real, tt.mul): lambda:
                generate_float_arithmetic('fmul'),
            (real, tt.div): lambda:
                generate_float_arithmetic('fdiv'),

            (real, tt.equal):
                lambda: generate_float_comparison('sete'),
            (real, tt.not_equal):
                lambda: generate_float_comparison('setne'),
            (real, tt.less):
                lambda: generate_float_comparison('setb'),
            (real, tt.less_or_equal):
                lambda: generate_float_comparison('setbe'),
            (real, tt.greater):
                lambda: generate_float_comparison('seta'),
            (real, tt.greater_or_equal):
                lambda: generate_float_comparison('setae'),
        }
        for key, func in BINARY_HANDLERS.iteritems():
            if key.count(integer) and key[-1] not in (tt.shr, tt.shl, tt.div):
                BINARY_HANDLERS[key] = integer_binary(func)

        left, right = binop.operands
        lvalue = binop.operation.type == tt.assign
        self.generate_statement(left, lvalue)
        self.generate_statement(right)
        # left type == right type
        operand_type = type(self.parser.expr_type(left))
        BINARY_HANDLERS[operand_type, binop.operation.type]()

    def generate_unary(self, unop):
        integer, real = SymTypeInt, SymTypeReal
        UNARY_HANDLERS = {
            (integer, tt.logic_not): lambda: self.cmd(
                ('pop', 'eax'),
                ('test', 'eax', 'eax'),
                ('sete', 'al'),
                ('movzx', 'eax', 'al'),
                ('push', 'eax'),
            ),

            (integer, tt.minus): lambda: self.cmd(
                ('pop', 'eax'),
                ('neg', 'eax'),
                ('push', 'eax'),
            ),

            (real, tt.minus): lambda: self.cmd(
                ('fld', self.stack()),
                'fchs',
                ('fstp', self.stack()),
            ),
        }

        operand = unop.operands[0]
        self.generate_statement(operand)
        operand_type = type(self.parser.expr_type(operand))
        UNARY_HANDLERS[operand_type, unop.operation.type]()
