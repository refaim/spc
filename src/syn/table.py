# -*- coding: utf-8 -*-

from UserDict import UserDict

from common.functions import *

class Symbol(object):
    @copy_args
    def __init__(self, name): pass
    def is_type(self): return False

    @property
    def symtable(self): return None

    def __str__(self):
        return self.name

class SymVar(Symbol):
    @copy_args
    def __init__(self, name, type, value): pass

    def __str__(self):
        text = '{0}: {1}'.format(self.name, self.type.name)
        if self.value:
            return '{0} = {1}'.format(text, self.value)
        else:
            return text

class SymConst(SymVar): pass

class SymFunctionArgument(SymVar):
    @copy_args
    def __init__(self, name, type, by_value): pass

class SymType(Symbol):
    def is_type(self): return True

class SymTypeFunction(SymType):
    @copy_args
    def __init__(self, name, args, restype, declarations, body): pass

    @property
    def symtable(self): return self._symtable

class SymTypeAlias(SymType):
    @copy_args
    def __init__(self, name, type): pass

    def __str__(self):
        return '{0} = {1}'.format(self.name, self.type.name)

class SymTypeArray(SymType):
    @copy_args
    def __init__(self, type, range):
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return 'array[{0}] of {1}'.format(self.range, self.type.name)
       
class SymTypeRange(SymType):
    @copy_args
    def __init__(self, leftbound, rightbound):
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return '{0}..{1}'.format(self.leftbound, self.rightbound)

class SymTypeRecord(SymType):
    def __init__(self, name, table):
        self._symtable = table
        SymType.__init__(self, name)

    @property
    def symtable(self): return self._symtable

class SymTypeInt(SymType):
    def __init__(self): 
        SymType.__init__(self, 'integer')

class SymTypeReal(SymType):
    def __init__(self): 
        SymType.__init__(self, 'real')


class SimpleSymTable(UserDict):
    def clean_type(self, symtype):
        try:
            return symtype.text
        except AttributeError:
            return symtype

    def write(self):
        if empty(self): 
            return
        print('Symbol table:')
        for sym, symtype in sorted(self.items()):
            print('{0}: {1}'.format(sym, self.clean_type(symtype)))

class SymTable(UserDict):
    def insert(self, symbol):
        assert isinstance(symbol, Symbol)
        self.__setitem__(symbol.name, symbol)
        return symbol

    def write(self, shift=''):
        def writeln(text): print shift + str(text)
        writeln('::symtable begin::')
        table = sorted(self.iteritems())
        for name, symbol in table:
            writeln(symbol)
            while hasattr(symbol, 'type'):
                symbol = symbol.type
                if symbol.symtable and not hasattr(symbol, 'written'):
                    symbol.symtable.write(shift + '\t')
                symbol.written = True
        writeln('::symtable end::')
