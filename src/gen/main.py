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
        self.symtable_stack = [self.parser.symtable]
        self.output = StringIO.StringIO()
        self.label_count = 0
        self.string_count = 0

    def find_symbol(self, name):
        for table in reversed(self.symtable_stack):
            if name in table:
                return table[name]

    def get_type(self, *expressions):
        return map(self.parser.expr_type, *expressions)

    def dword(self, arg):
        return asm.SizeCast('dword', arg)

    def allocate(self, name, size, dup=True):
        self.declarations.append(asm.Declaration(name, size, dup))

    def generate_label(self, name):
        self.instructions.append(asm.Label(name))

    def generate_command(self, *commands):
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

    def get_labels(self, count=1):
        result = []
        for i in range(count):
            self.label_count += 1
            result.append('L' + str(self.label_count))
        return result[0] if len(result) == 1 else result

    def get_string_name(self):
        self.string_count += 1
        return 'S' + str(self.string_count)

    TYPE2STR = {
        SymTypeInt:    'int',
        SymTypeReal:   'real',
        SymTypeArray:  'arr',
        SymTypeRecord: 'rec',
    }
    def get_variable_name(self, name, type_):
        return '{0}${1}'.format(self.TYPE2STR[type(type_.type)], name)

    def get_variable_offset(self, name):
        symbol = self.find_symbol(name)
        return self.dword(asm.MemoryOffset(symbol.gen_name))

    def generate(self):
        self.output.write(HEADER)

        # avoid bug with iteration over UserDict (Python 2.6.4)
        table = dict(self.parser.symtable)

        # reserve memory for global variables
        for name, type_ in table.iteritems():
            if isinstance(type_, (SymVar, SymConst)):
                gen_name = self.get_variable_name(name, type_)
                self.allocate(gen_name, type_.size)
                table[name].gen_name = gen_name

        self.generate_label('main')
        self.generate_statement(self.program)

        if is_windows():
            self.generate_command(
                'stdcall', asm.MemoryOffset('ExitProcess'), 0)
        else:
            self.generate_command(
                ('mov', 'eax', 0),
                'ret',
            )

        def write_list(list_):
            for i, row in enumerate(list_):
                self.output.write(str(row) +
                    ('\n' if i < len(list_) - 1 else ''))

        if self.declarations:
            self.output.write("section '.data' readable writeable\n\n")
            write_list(self.declarations)
            self.output.write('\n\n')

        self.output.write("section '.code' readable executable\n\n")
        write_list(self.instructions)

        self.output.write('\n')
        return self.output.getvalue()

    def generate_statement(self, stmt):

        def jump_if_zero(label):
            self.generate_command(
                ('pop', 'eax'),
                ('test', 'eax', 'eax'),
                ('jz', label),
            )

        def generate_operation():
            if len(stmt.operands) == 2:
                self.generate_binary(stmt)
            else:
                self.generate_unary(stmt)

        def generate_write():
            map(self.generate_statement, reversed(stmt.args))
            if len(stmt.args) > 1:
                format_string = ''.join(['%d'] * len(stmt.args))
            else:
                format_string = '%d'
            if stmt.newline:
                postfix = '10, 0'
            else:
                postfix = '0'
            format_string = "'{0}', {1}".format(format_string, postfix)
            format_string_name = self.get_string_name()
            self.allocate(format_string_name, format_string, dup=False)
            self.generate_command(
                ('push', format_string_name),
                ('call', asm.MemoryOffset('printf')),
                ('add', 'esp', 4 * (len(stmt.args) + 1)),
            )

        def generate_variable():
            self.generate_command('push', self.get_variable_offset(stmt.name))

        def generate_while():
            start, end = self.get_labels(2)
            self.loops.append((start, end))
            self.generate_label(start)
            self.generate_statement(stmt.condition)
            jump_if_zero(end)
            self.generate_statement(stmt.action)
            self.generate_command('jmp', start)
            self.generate_label(end)
            self.loops.pop()

        def generate_repeat():
            start, end = self.get_labels(2)
            self.loops.append((start, end))
            self.generate_label(start)
            self.generate_statement(stmt.action)
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
            self.generate_command(
                'inc', self.get_variable_offset(stmt.counter.name))
            self.generate_command('jmp', start)
            self.generate_label(end)
            self.loops.pop()

        def generate_if():
            self.generate_statement(stmt.condition)
            else_case, endif = self.get_labels(2)
            jump_if_zero(else_case)
            self.generate_statement(stmt.action)
            self.generate_command('jmp', endif)
            self.generate_label(else_case)
            if stmt.else_action:
                self.generate_statement(stmt.else_action)
            self.generate_label(endif)

        def generate_block():
            for statement in stmt.statements:
                self.generate_statement(statement)

        handlers = {
            SynOperation: generate_operation,
            SynStatementIf: generate_if,
            SynStatementFor: generate_for,
            SynStatementWhile: generate_while,
            SynStatementRepeat: generate_repeat,
            SynStatementBreak: lambda:
                self.generate_command('jmp', self.loops[-1][1]),
            SynStatementContinue: lambda:
                self.generate_command('jmp', self.loops[-1][0]),
            SynStatementBlock: generate_block,
            SynStatementWrite: generate_write,
            SynVar: generate_variable,
            SynConst: lambda: self.generate_command('push', stmt.name),
            SynEmptyStatement: lambda: self.generate_command('nop'),
        }
        handlers[type(stmt)]()

    def generate_binary(self, binop):

        def generate_assignment():
            dest = self.get_variable_offset(binop.operands[0].name)
            self.generate_command('mov', dest, 'ebx')

        def generate_logic_or():
            true, false, end = self.get_labels(3)
            self.generate_command(
                ('test', 'eax', 'eax'),
                ('jnz', true),
                ('test', 'ebx', 'ebx'),
                ('jz', false),
            )
            self.generate_label(true)
            self.generate_command(
                ('mov', 'eax', 1),
                ('jmp', end),
            )
            self.generate_label(false)
            self.generate_command('xor', 'eax', 'eax')
            self.generate_label(end)
            self.generate_command('push', 'eax')

        def generate_logic_and():
            false, end = self.get_labels(2)
            self.generate_command(
                ('test', 'eax', 'eax'),
                ('jz', false),
                ('test', 'ebx', 'ebx'),
                ('jz', false),
                ('mov', 'eax', 1),
                ('jmp', end),
            )
            self.generate_label(false)
            self.generate_command('xor', 'eax', 'eax')
            self.generate_label(end)
            self.generate_command('push', 'eax')

        def generate_comparison(setcc):
            self.generate_command(
                ('cmp', 'eax', 'ebx'),
                (setcc, 'al'),
                ('movzx', 'eax', 'al'),
                ('push', 'eax'),
            )

        def generate_shift(shift):
            self.generate_command(
                ('pop', 'ecx'),
                ('pop', 'eax'),
                (shift, 'eax', 'cl'),
                ('push', 'eax'),
            )

        def generate_real_arithmetic(command):
            self.generate_command(
                ('fld', self.dword(asm.RegOffset('esp', 4))),
                (command, self.dword('esp')),
                ('add', 'esp', 4),
                ('fstp', self.dword('esp')),
            )

        def integer_binary(function):
            @functools.wraps(function)
            def wraps(**kwargs):
                self.generate_command(
                    ('pop', 'ebx'),
                    ('pop', 'eax'),
                )
                return function(**kwargs)
            return wraps

        generate = self.generate_command
        integer, real = SymTypeInt, SymTypeReal
        BINARY_HANDLERS = {
            (integer, integer, tt.assign): generate_assignment,

            (integer, integer, tt.plus): lambda: generate(
                ('add', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, integer, tt.minus): lambda: generate(
                ('sub', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, integer, tt.mul): lambda: generate(
                ('imul', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, integer, tt.int_div): lambda: generate(
                ('xor', 'edx', 'edx'),
                ('idiv', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, integer, tt.int_mod): lambda: generate(
                ('xor', 'edx', 'edx'),
                ('idiv', 'ebx'),
                ('push', 'edx'),
            ),

            (integer, integer, tt.equal):
                lambda: generate_comparison('sete'),
            (integer, integer, tt.less):
                lambda: generate_comparison('setl'),
            (integer, integer, tt.less_or_equal):
                lambda: generate_comparison('setle'),
            (integer, integer, tt.greater):
                lambda: generate_comparison('setg'),
            (integer, integer, tt.greater_or_equal):
                lambda: generate_comparison('setge'),
            (integer, integer, tt.not_equal):
                lambda: generate_comparison('setne'),

            (integer, integer, tt.logic_or): generate_logic_or,
            (integer, integer, tt.logic_and): generate_logic_and,
            (integer, integer, tt.logic_xor): lambda: generate(
                ('xor', 'eax', 'ebx'),
                ('push', 'eax'),
            ),

            (integer, integer, tt.shr): lambda: generate_shift('shr'),
            (integer, integer, tt.shl): lambda: generate_shift('shl'),

            (real, real, tt.plus): lambda:
                generate_real_arithmetic('fadd'),
            (real, real, tt.minus): lambda:
                generate_real_arithmetic('fsub'),
            (real, real, tt.mul): lambda:
                generate_real_arithmetic('fmul'),
            (real, real, tt.div): lambda:
                generate_real_arithmetic('fdiv'),
            (integer, integer, tt.div): lambda:
                generate_real_arithmetic('fdiv'),
        }
        for key, func in BINARY_HANDLERS.iteritems():
            if key.count(integer) == 2 and tt.shr != key[-1] != tt.shl:
                BINARY_HANDLERS[key] = integer_binary(func)

        map(self.generate_statement, binop.operands)
        ltype, rtype = map(type, self.get_type(binop.operands))
        BINARY_HANDLERS[ltype, rtype, binop.operation.type]()

    def generate_unary(self, unop):
        generate = self.generate_command
        integer, real = SymTypeInt, SymTypeReal
        UNARY_HANDLERS = {
            (integer, tt.logic_not): lambda: generate(
                ('pop', 'eax'),
                ('test', 'eax', 'eax'),
                ('sete', 'al'),
                ('movzx', 'eax', 'al'),
                ('push', 'eax'),
            ),

            (integer, tt.minus): lambda: generate(
                ('pop', 'eax'),
                ('neg', 'eax'),
                ('push', 'eax'),
            ),
        }

        self.generate_statement(unop.operands[0])
        optype = self.get_type(unop.operands)[0]
        UNARY_HANDLERS[type(optype), unop.operation.type]()
