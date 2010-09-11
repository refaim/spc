# -*- coding: utf-8 -*-

from UserDict import UserDict

import lib.enum as enum
from common.functions import *

class Symbol(object):
    def __init__(self, sname):
        self._name = sname
        self._prefix = ''

    @property 
    def is_type(self): return False
    @property
    def name(self): return self._name
    @property
    def symtable(self): return None

    def __str__(self):
        return self.name

class SymVar(Symbol):
    def __init__(self, sname, stype, svalue):
        Symbol.__init__(self, sname)
        self._type = stype
        self._value = svalue

    @property
    def type(self): return self._type
    @property
    def value(self): return self._value

    @property
    def prefix(self): return 'var'

class SymConst(SymVar):
    @property
    def prefix(self): return 'const'

class SymFunction(Symbol):
    def __init__(self, ftype, fname, fargs=None):
        Symbol.__init__(self, fname)
        self._ftype = ftype
        #self.args = fargs or SymTable()
        self.args = fargs
        self._symtable = SymTable()

    @property
    def symtable(self): return self._symtable

    @property
    def prefix(self): return 'function'


class SymType(Symbol):
    @property
    def is_type(self): return True

    @property
    def prefix(self): return 'type'

class SymTypeAlias(SymType):
    def __init__(self, sname, target):
        SymType.__init__(self, sname)
        self.target = target

    def __str__(self):
        name = SymType.__str__(self)
        return '{0} (alias to "{1}")'.format(name, self.target)

class SymTypeArray(SymType):
    def __init__(self, basetype, range):
        self.basetype, self.range = basetype, range
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return 'array[{0}] of {1}'.format(self.range, self.basetype)
       
class SymTypeRange(SymType):
    def __init__(self, leftbound, rightbound):
        self.leftbound, self.rightbound = leftbound, rightbound
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return '{0}..{1}'.format(self.leftbound, self.rightbound)
        
    @property
    def prefix(self): return 'range'

class SymTypeRecord(SymType):
    #def __init__(self, sname, types):
    #    SymType.__init__(self, sname)
    #    self.symtable = SymTable(types)

    @property
    def symtable(self): return self._symtable

class SymTypeInt(SymType):
    def __init__(self): 
        SymType.__init__(self, 'integer')

class SymTypeReal(SymType):
    def __init__(self): 
        SymType.__init__(self, 'real')

class SimpleSymTable(UserDict):
    def write(self):
        if empty(self): 
            return
        print("Symbol table:")
        for sym, symtype in sorted(self.items()):
            print("{0}: {1}".format(sym, symtype))

class SymTable(UserDict):
    def __init__(self):
        UserDict.__init__(self)
        self.insert(SymTypeInt())
        self.insert(SymTypeReal())

    def insert(self, smb):
        assert isinstance(smb, Symbol)
        self.__setitem__(smb.name, smb)
        return smb

    def write(self, shift=''):
        for symbolname, symboltype in sorted(self.items()):
            text = shift + '[' + symboltype.prefix + ']'
            if symboltype.is_type:
                text = '{0} {1}'.format(text, symboltype)
            else:
                realtype = symboltype.type
                text = '{0} {1}: {2!s}'.format(
                    text, symbolname, realtype.name)
                if isinstance(symboltype, SymConst):
                    text = '{0} = {1}'.format(text, symboltype.value)
                if realtype.symtable:
                    realtype.symtable.write(shift + '\t')
            print(text)
