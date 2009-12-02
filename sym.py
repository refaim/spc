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
    def has_symtable(self): return False

    @property
    def symtype(self): return st.symtype

class SymVar(Symbol):
    def __init__(self, sname, stype):
        Symbol.__init__(self, sname)
        self._type = stype

    @property
    def symtype(self): return st.variable
    def get_type(self): return self._type

class SymFunction(Symbol):
    def __init__(self, ftype, fname):
        Symbol.__init__(self, fname)
        self._ftype = ftype
        self.args = SymbolTable()

    @property
    def symtype(self): return st.function
    def has_symtable(self): return True

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
    def __init__(self, sname, types):
        SymType.__init__(self, sname)
        self.symtable = SymTable(types)

    @property
    def symtype(self): return st.record
    def has_symtable(self): return True

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
        if empty(self): return
        print("Symbol table:")
        for sym, symtype in sort(self.items()):
            print("{0}: {1}".format(sym, symtype))

class SymTable(SimpleSymTable):
    def __init__(self, types = None):
        SimpleSymTable.__init__(self)
        if types is None:
            types = [SymTypeInt(), SymTypeFloat()]
        for entry in types:
            self.insert(entry)

    def insert(self, smb):
        if not isinstance(smb, Symbol):
            raise SymTableError
        self.__setitem__(smb.get_name(), smb)

    def write(self, shift = ''):
        if empty(self): return
        items = ((sname, stype) for sname, stype in sort(self.items()))
        check = lambda t: not isinstance(t, SymType)
        for n, t in items:
            if check(t):
                tname = t.get_type().get_name()
                print('{0}: {1}'.format(shift + n, tname))
                if t.get_type().has_symtable():
                    newshift = shift + '\t'
                    t.get_type().symtable.write(newshift)
            else:
                if n not in ('float', 'integer'):
                    print(shift + n)
