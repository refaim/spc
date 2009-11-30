# -*- coding: utf-8 -*-

from UserDict import UserDict

from enum import Enum
from common import *

# SymbolType
st = Enum("symtype", "variable", "array", "record", "function", "integer", "float")

class Symbol(object):
    def __init__(self, sname):
        self._name = sname

    def is_type(self): return False
    def get_name(self): return self._name
    def get_type(self): st.symtype

class SymVariable(Symbol):
    def __init__(self, stype, sname):
        Symbol.__init__(self, sname)
        self._type = stype

    def get_type(self): return st.variable

class SymType(Symbol):
    def is_type(self): return True
    def get_type(self): return st.symtype

class SymTypeArray(SymType):
    def get_type(self): return st.array

class SymTypeRecord(SymType):
    def get_type(self): return st.record

class SymTypeFunction(SymType):
    def get_type(self): return st.function

class SymTypeInt(SymType):
    def get_type(self): return st.integer

class SymTypeFloat(SymType):
    def get_type(self): return st.float

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
