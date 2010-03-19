# -*- coding: utf-8 -*-

from UserDict import UserDict

from enum import Enum

from common import *

# SymbolType
st = Enum("symtype", "variable", "array", "record", "function", "range", \
          "integer", "real", "const")

class Symbol(object):
    def __init__(self, sname):
        self._name = sname

    def istype(self): return False
    def getname(self): return self._name
    def hassymtable(self): return False

    @property
    def symtype(self): return st.symtype

class SymVar(Symbol):
    def __init__(self, sname, stype, svalue):
        Symbol.__init__(self, sname)
        self._type = stype
        self._value = svalue

    @property
    def symtype(self): return st.variable
    def gettype(self): return self._type

class SymConst(SymVar):
    @property
    def symtype(self): return st.const

class SymFunction(Symbol):
    def __init__(self, ftype, fname, fargs=None):
        Symbol.__init__(self, fname)
        self._ftype = ftype
        self.args = fargs or SymTable()
        self.symtable = SymTable()

    @property
    def symtype(self): return st.function
    def hassymtable(self): return True

class SymArray(Symbol):
    pass#def __init__

class SymType(Symbol):
    def istype(self): return True

    @property
    def symtype(self): return st.symtype

class SymTypeArray(SymType):
    @property
    def symtype(self): return st.array

class SymTypeRecord(SymType):
    def __init__(self, sname, types):
        SymType.__init__(self, sname)
        self.symtable = SymTable(types)

    @property
    def symtype(self): return st.record
    def hassymtable(self): return True

class SymTypeFunction(SymType):
    @property
    def symtype(self): return st.function

class SymTypeInt(SymType):
    def __init__(self): SymType.__init__(self, 'integer')
    @property
    def symtype(self): return st.integer

class SymTypeReal(SymType):
    def __init__(self): SymType.__init__(self, 'real')
    @property
    def symtype(self): return st.real

class SymTypeRange(SymType):
    @property
    def symtype(self): return st.range

class SimpleSymTable(UserDict):
    def write(self):
        if empty(self): 
            return
        print("Symbol table:")
        for sym, symtype in sorted(self.items()):
            print("{0}: {1}".format(sym, symtype))

class SymTable(SimpleSymTable):
    def __init__(self, types=None):
        SimpleSymTable.__init__(self)
        if types is None:
            types = [SymTypeInt(), SymTypeReal()]
        for entry in types:
            self.insert(entry)

    def insert(self, smb):
        assert isinstance(smb, Symbol)
        self.__setitem__(smb.getname(), smb)

    def write(self, shift=''):
        if empty(self): 
            return
        for sname, stype in sorted(self.items()):
            if not isinstance(stype, SymType):
                tname = stype.gettype().getname()
                print('{0}: {1}'.format(shift + sname, tname))
                if stype.gettype().hassymtable():
                    stype.gettype().symtable.write(shift + '\t')
            else:
                print(shift + sname)
