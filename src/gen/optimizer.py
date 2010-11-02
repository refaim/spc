# -*- coding: utf-8 -*-

import math

from common.functions import copy_args, rlist
import asm

REGISTERS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')


class Optimizer(object):
    @copy_args
    def __init__(self, instructions):
        self.changed = True
        self.pos = 0
        self.current_slice_len = -1
        self.optimizers = [attr for attr in dir(self)
            if attr.startswith('optimize_')]

    def is_imm(self, arg):
        return isinstance(arg, (int, float))

    def is_reg(self, arg):
        return arg in REGISTERS

    def replace(self, commands):
        if not isinstance(commands, (list, tuple)):
            commands = [commands]
        self.instructions = (
            self.instructions[:self.pos] +
            list(commands) +
            self.instructions[self.pos+self.current_slice_len:])
        self.changed = True

    def remove(self):
        del self.instructions[self.pos:self.pos+self.current_slice_len]
        self.changed = True

    def sequence(self, *commands):

        def mnem_list(window):
            result = []
            for cmd in window:
                if not isinstance(cmd, asm.Command):
                    return None
                cmd = getattr(cmd, 'mnem')
                if cmd.startswith('set'):
                    cmd = 'setcc'
                result.append(cmd)
            return result

        window = self.instructions[self.pos:self.pos+len(commands)]
        if list(commands) == mnem_list(window):
            self.current_slice_len = len(commands)
            return window
        return None

    def find_near_label(self, name):
        for label in self.instructions[self.pos+1:]:
            if not isinstance(label, asm.Label):
                return None
            if label.name == name:
                return True

    def optimize(self):
        while self.changed:
            self.changed = False
            while self.pos < len(self.instructions):
                for func in self.optimizers:
                    getattr(self, func)()
                self.pos += 1
            self.pos = 0
        return self.instructions

    def optimize_push_pop(self):
        '''
        push a
        push b
        pop c
        pop d
        ------->
        mov d, a
        mov c, b
        '''
        slc = self.sequence('push', 'push', 'pop', 'pop')
        if slc:
            self.replace((
                asm.Command('mov', slc[3].arg, slc[0].arg),
                asm.Command('mov', slc[2].arg, slc[1].arg),
            ))

        '''
        push reg/mem
        pop reg/mem
        -->
        mov reg/mem, reg/mem
        '''
        slc = self.sequence('push', 'pop')
        if slc:
            self.replace(asm.Command('mov', slc[1].arg, slc[0].arg))

    def optimize_call(self):
        '''
        mov eax, func
        call eax
        -->
        call func
        '''
        slc = self.sequence('mov', 'call')
        if (slc and slc[0].args[0] == slc[1].arg):
            self.replace(asm.Command('call', slc[0].args[1]))

    def optimize_arithmetic(self):

        slc = self.sequence('sub')
        if slc:
            # remove 'sub reg/mem, 0'
            if slc[0].args[1] == 0:
                self.remove()
            # 'sub reg/mem, 1' --> 'dec reg/mem'
            elif slc[0].args[1] == 1:
                self.replace(asm.Command('dec', slc[0].args[0]))

        slc = self.sequence('add')
        if slc:
            # remove 'add reg/mem, 0'
            if slc[0].args[1] == 0:
                self.remove()
            # 'add reg/mem, 1' --> 'inc reg/mem'
            elif slc[0].args[1] == 1:
                self.replace(asm.Command('inc', slc[0].args[0]))
            # 'add reg/mem, -a' --> 'sub reg/mem, a'
            elif slc[0].args[1] < 0:
                self.replace(asm.Command('sub', slc[0].args[0], -slc[0].args[1]))


        def is_power(arg):
            log = math.log(arg, 2)
            if log == int(log):
                return int(log)

        # 'imul reg, 2^n' --> 'shl eax, n'
        slc = self.sequence('imul')
        if slc and len(slc[0].args) > 1 and self.is_imm(slc[0].args[1]):
            value = is_power(slc[0].args[1])
            if value:
                self.replace(asm.Command('shl', slc[0].args[0], value))

    def optimize_mov_and_arithmetic(self):
        slc = self.sequence('add', 'mov')
        '''
        add a, b
        mov b, a
        -->
        add b, a
        '''
        if (slc and
            slc[0].args == rlist(slc[1].args) and
            not self.is_imm(slc[0].args[1])
        ):
            self.replace(asm.Command(
                'add', slc[0].args[1], slc[0].args[0]))

        '''
        mov reg1, reg/mem
        add reg2, reg1
        -->
        add reg2, reg/mem
        '''
        slc = self.sequence('mov', 'add')
        if (slc and
            slc[0].args[0] == slc[1].args[1] and
            self.is_reg(slc[1].args[0])
        ):
            self.replace(asm.Command('add', slc[1].args[0], slc[0].args[1]))

        '''
        mov reg/mem, imm
        neg reg/mem
        -->
        mov reg/mem, -imm
        '''
        slc = self.sequence('mov', 'neg')
        if (slc and
            slc[0].args[0] == slc[1].arg and
            self.is_imm(slc[0].args[1])
        ):
            self.replace(asm.Command('mov', slc[0].args[0], -slc[0].args[1]))

        '''
        mov reg, 1
        dec reg
        -->
        xor reg, reg
        '''
        slc = self.sequence('mov', 'dec')
        if (slc and
            self.is_imm(slc[0].args[1]) and
            self.is_reg(slc[1].arg) and
            slc[0].args[0] == slc[1].arg
        ):
            self.replace(asm.Command('mov', slc[1].arg, slc[0].args[1] - 1))

        '''
        mov reg, imm1
        shl reg, imm2
        -->
        mov reg, imm1 * (2 ** imm2)
        '''
        slc = self.sequence('mov', 'shl')
        if (slc and
            slc[0].args[0] == slc[1].args[0] and
            self.is_imm(slc[0].args[1]) and
            self.is_imm(slc[1].args[1])
        ):
            self.replace(asm.Command(
                'mov', slc[0].args[0],
                       slc[0].args[1] * (2 ** slc[1].args[1])))

    def optimize_mov(self):
        '''
        mov a, imm
        mov reg/mem, a
        -->
        mov reg/mem, imm
        '''
        slc = self.sequence('mov', 'mov')
        if slc:
            if (slc[0].args[0] == slc[1].args[1] and
                self.is_imm(slc[0].args[1])
            ):
                self.replace(asm.Command('mov', slc[1].args[0], slc[0].args[1]))

            '''
            mov reg, offset
            mov dword [reg], imm
            -->
            mov dword [offset], imm
            '''
            if (isinstance(slc[1].args[0], asm.SizeCast) and
                self.is_reg(slc[0].args[0]) and
                slc[0].args[0] == slc[1].args[0].arg.reg and
                self.is_imm(slc[1].args[1])
            ):
                cast = slc[1].args[0]
                cast.arg.reg = slc[0].args[1]
                self.replace(asm.Command('mov', cast, slc[1].args[1]))

        slc = self.sequence('mov')
        if not slc:
            return

        # 'mov reg, 0' --> 'xor reg, reg'
        if self.is_reg(slc[0].args[0]) and slc[0].args[1] == 0:
            self.replace(asm.Command('xor', slc[0].args[0], slc[0].args[0]))

        # remove 'mov reg/mem, reg/mem'
        elif slc[0].args[0] == slc[0].args[1]:
            self.remove()

    def optimize_jmp(self):
        '''
        jmp label
        (labels)*
        label:
        -->
        (labels)*
        label:
        '''
        slc = self.sequence('jmp')
        if slc and self.find_near_label(slc[0].arg):
            self.remove()

    def optimize_loop(self):
        '''
        setcc reg8
        movzx reg16, reg8
        test reg16, reg16
        -->
        setcc reg8
        test reg8, reg8
        '''
        slc = self.sequence('setcc', 'movzx', 'test')
        if (slc and
            slc[0].arg == slc[1].args[1] and
            slc[1].args[0] == slc[2].args[0] == slc[2].args[1]
        ):
            self.replace((
                slc[0],
                asm.Command('test', slc[0].arg, slc[0].arg),
            ))

        '''
        mov eax, offset
        inc dword [eax]
        -->
        inc dword [offset]
        '''
        slc = self.sequence('mov', 'inc')
        if (slc and
            isinstance(slc[1].arg, asm.SizeCast) and
            slc[0].args[0] == slc[1].args[0].arg.reg and
            self.is_reg(slc[0].args[0])
        ):
            self.replace(asm.Command(
                'inc', asm.SizeCast('dword', asm.Offset(slc[0].args[1]))))

        '''
        mov eax, ebp
        sub eax, offset
        inc dword [eax]
        -->
        inc dword [ebp-offset]
        '''
        slc = self.sequence('mov', 'sub', 'inc')
        if (slc and
            isinstance(slc[2].arg, asm.SizeCast) and
            slc[0].args[0] == slc[1].args[0] == slc[2].args[0].arg.reg and
            self.is_reg(slc[0].args[1]) and
            self.is_imm(slc[1].args[1])
        ):
            self.replace(asm.Command(
                'inc', asm.SizeCast(
                    'dword', asm.Offset(slc[0].args[1], -slc[1].args[1]))))

