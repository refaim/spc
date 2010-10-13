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

if 'win' in sys.platform:
    HEADER = \
'''\
format PE
entry main

include '{0}'

data import
    library msvcrt, 'MSVCRT.DLL'
    import msvcrt, printf, 'printf'
end data\n
'''.format(os.path.join(FASM_PATH, 'import32.inc'))

else:
    HEADER = \
'''\
format ELF

public main
extrn printf\n
'''

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

    def get_label(self, count=1):
        result = []
        for i in range(count):
            self.label_count += 1
            result.append('L' + str(self.label_count))
        return result

    TYPE2STR = {
        SymTypeInt:    'int',
        SymTypeReal:   'real',
        SymTypeArray:  'arr',
        SymTypeRecord: 'rec',
    }
    def get_variable_name(self, name, type_):
        return '{0}${1}'.format(self.TYPE2STR[type(type_.type)], name)

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
        self.generate_command(
            ('mov', 'eax', 0),
            'ret',
        )

        def write_list(list_):
            for i, row in enumerate(list_):
                self.output.write(str(row) +
                    ('\n' if i < len(list_) - 1 else ''))


        if self.declarations:
            self.output.write("section '.data' writeable\n")
            write_list(self.declarations)
            self.output.write('\n\n')

        self.output.write("section '.text' executable\n\n")
        write_list(self.instructions)

        return self.output.getvalue()

    def generate_statement(self, stmt):

        def generate_cast():
            target = self.cast_to_dword(asm.RegOffset('esp'))
            self.generate_command(
                ('fild', target),
                ('fstp', target),
            )

        def generate_operation():
            if len(stmt.operands) == 2:
                self.generate_binary(stmt)
            else:
                self.generate_unary(stmt)

        def generate_block():
            for statement in stmt.statements:
                self.generate_statement(statement)

        handlers = {
            SynOperation: generate_operation,
            SynCastToReal: generate_cast,
            SynStatementBlock: generate_block,
            SynEmptyStatement: lambda: self.generate_command('nop'),
            SynConst: lambda: self.generate_command('push', stmt.name),
            SynVar: lambda: self.generate_command(
                'push', self.find_symbol(stmt.name).gen_name),
        }
        handlers[type(stmt)]()

    def generate_binary(self, binop):

        def generate_assignment():
            dest = self.find_symbol(binop.operands[0].name)
            cast_to_dest = functools.partial(self.cast_size, dest.size)
            self.generate_command(
                ('mov', 'eax', 'ebx'),
                ('mov', cast_to_dest(
                    asm.MemoryOffset(dest.gen_name)), 'eax'),
            )

        def generate_logic_or():
            true, false, end = self.get_label(3)
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
            false, end = self.get_label(2)
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

        def generate_logic_xor():
            first_false, true, false, end = self.get_label(4)
            self.generate_command(
                ('test', 'eax', 'eax'),
                ('jz', first_false),
                ('test', 'ebx', 'ebx'),
                ('jz', true),
                ('jmp', false),
            )
            self.generate_label(first_false)
            self.generate_command(
                ('test', 'ebx', 'ebx'),
                ('jnz', true),
            )
            self.generate_label(true)
            self.generate_command(
                ('mov', 'eax', 1),
                ('jmp', end),
            )
            self.generate_label(false)
            self.generate_command('xor', 'eax', 'eax')
            self.generate_command('push', 'eax')
            self.generate_label(end)

        def generate_comparison(setter):
            self.generate_command(
                ('cmp', 'eax', 'ebx'),
                (setter, 'al'),
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

            (integer, integer, tt.equal): lambda: generate_comparison('sete'),
            (integer, integer, tt.less): lambda: generate_comparison('setl'),
            (integer, integer, tt.less_or_equal): lambda: generate_comparison('setle'),
            (integer, integer, tt.greater): lambda: generate_comparison('setg'),
            (integer, integer, tt.greater_or_equal): lambda: generate_comparison('setge'),
            (integer, integer, tt.not_equal): lambda: generate_comparison('setne'),

            (integer, integer, tt.logic_or): generate_logic_or,
            (integer, integer, tt.logic_and): generate_logic_and,
            (integer, integer, tt.logic_xor): generate_logic_xor,

            (integer, integer, tt.shr): lambda: generate_shift('shr'),
            (integer, integer, tt.shl): lambda: generate_shift('shl'),
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

            (real, tt.minus): lambda: generate(
                ('fld', self.get_dword_from_stack()),
                'fchs',
                ('fstp', self.get_dword_from_stack()),
            ),
        }

        self.generate_statement(unop.operands[0])
        optype = self.get_type(unop.operands)
        UNARY_HANDLERS[type(optype), unop.operation.type]()
