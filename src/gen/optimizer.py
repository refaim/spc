# -*- coding: utf-8 -*-

from common.functions import copy_args
import asm

WINDOW_SIZE = 2

REGISTERS = ('eax', 'ebx', 'ecx', 'edx', 'ebp', 'esi', 'edi')

class Optimizer(object):
    @copy_args
    def __init__(self, instructions):
        self.changed = True
        self.left = 0

    def replace(self, commands, count=WINDOW_SIZE):
        if not isinstance(commands, (list, tuple)):
            commands = [commands]
        self.instructions = self.instructions[:self.left] + list(commands) + self.instructions[self.left+count:]
        self.changed = True

    def remove(self, count):
        del self.instructions[self.left:self.left+count]

    def is_command(self, command):
        current = self.instructions[self.left]
        return isinstance(current, asm.Command) and command == current.mnem

    def is_sequence(self, *commands):
        window = self.instructions[self.left:self.left+len(commands)]
        if not all(isinstance(cmd, asm.Command) for cmd in window):
            return False
        return list(commands) == [getattr(cmd, 'mnem') for cmd in window]

    def get_slice(self, length):
        return self.instructions[self.left:self.left+length]

    def optimize(self):
        while self.changed:
            self.changed = False
            while self.left + WINDOW_SIZE < len(self.instructions):
                self.optimize_push_pop()
                self.optimize_mov()
                self.left += 1
            self.left = 0
        return self.instructions

    def optimize_push_pop(self):
        if self.is_sequence('push', 'push', 'pop', 'pop'):
            c = self.get_slice(4)
            self.replace((
                asm.Command('mov', c[3].arg, c[0].arg),
                asm.Command('mov', c[2].arg, c[1].arg),
            ), 4)

        if self.is_sequence('push', 'pop'):
            c = self.get_slice(2)
            self.replace(asm.Command('mov', c[1].arg, c[0].arg))

    def optimize_mov(self):
        if self.is_command('mov'):
            c = self.get_slice(1)[0]

            if c.args[0] in REGISTERS and c.args[1] == 0:
                self.replace(asm.Command('xor', c.args[0], c.args[0]), 1)

            if c.args[0] == c.args[1]:
                self.remove(1)
