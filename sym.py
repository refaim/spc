# -*- coding: utf-8 -*-

from UserDict import UserDict

from enum import Enum
from common import *

# SymbolType
st = Enum("symtype", "variable", "array", "record", "function", "range", \
          "integer", "float")

class Symbol(object):
    def __init__(self, sname):
        self._name = sname

    def is_type(self): return False
    def get_name(self): return self._name

    @property
    def symtype(self): return st.symtype

class SymVar(Symbol):
    def __init__(self, sname, stype):
        Symbol.__init__(self, sname)
        self._type = stype

    @property
    def symtype(self): return st.variable

class SymFunction(Symbol):
    def __init__(self, ftype, fname):
        Symbol.__init__(self, fname)
        self._ftype = ftype
        self.args = SymbolTable()

    @property
    def symtype(self): return st.function

class SymArray(Symbol):
    pass#def __init__

class SymType(Symbol):
    def is_type(self): return True

    @property
    def symtype(self): return st.symtype

class SymTypeArray(SymType):
    @property
    def symtype(self): return st.array

class SymTypeRecord(SymType):
    @property
    def symtype(self): return st.record

class SymTypeFunction(SymType):
    @property
    def symtype(self): return st.function

class SymTypeInt(SymType):
    def __init__(self): SymType.__init__(self, 'integer')
    @property
    def symtype(self): return st.integer

class SymTypeFloat(SymType):
    def __init__(self): SymType.__init__(self, 'float')
    @property
    def symtype(self): return st.float

class SymTypeRange(SymType):
    @property
    def symtype(self): return st.range

# для контроля
class SymTableError(Exception): pass

class SimpleSymTable(UserDict):
    def write(self):
        if not empty(self):
            print("Symbol table:")
            for sym, symtype in sort(self.items()):
                print("{0}: {1}".format(sym, symtype))

class SymTable(SimpleSymTable):
    def insert(self, smb):
        if not isinstance(smb, Symbol):
            raise SymTableError
        self.__setitem__(smb.get_name(), smb)
