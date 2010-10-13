# -*- coding: utf-8 -*-

from common.functions import copy_args

class Base(object): 
    pass

class Declaration(Base):
    @copy_args
    def __init__(self, name, value, dup): pass
    def __str__(self):
        text = '{0} db {1}'.format(self.name, self.value)
        if self.dup:
            text = '{0} dup(0)'.format(text)
        return text

class Label(Base):
    @copy_args
    def __init__(self, name): pass
    def __str__(self):
        return self.name + ':'

class Command(Base):
    @copy_args
    def __init__(self, mnemonics, *args):
        self.args = args
    def __str__(self):
        text = self.mnemonics
        if self.args:
            text += ' ' + ', '.join(str(arg) for arg in self.args)
        return text

class Offset(Base):
    @copy_args
    def __init__(self, reg, offset=0): pass
    def __str__(self):
        text = self.reg
        if self.offset:
            text += ('+{0}' if self.offset > 0 else '{0}').format(self.offset)
        return '[{0}]'.format(text)

class SizeCast(Base):
    @copy_args
    def __init__(self, size, arg): pass
    def __str__(self):
        return '{0} {1!s}'.format(self.size, self.arg)
