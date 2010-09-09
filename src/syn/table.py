# -*- coding: utf-8 -*-

from UserDict import UserDict

from common.functions import *
import lib.enum as enum

# SymbolType
st = enum.Enum("symtype", "variable", "array", "record", "function", \
    "procedure", "range", "integer", "real", "const")

class Symbol(object):
    def __init__(self, sname):
        self._name = sname
        self._prefix = ''

    def istype(self): return False
    def getname(self): return self._name
    def hassymtable(self): return False

    def __str__(self):
        return self.getname()

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
    def getprefix(self): return 'var'
    def getvalue(self): return self._value

class SymConst(SymVar):
    @property
    def symtype(self): return st.const
    def getprefix(self): return 'const'

class SymFunction(Symbol):
    def __init__(self, ftype, fname, fargs=None):
        Symbol.__init__(self, fname)
        self._ftype = ftype
        self.args = fargs or SymTable()
        self.symtable = SymTable()

    @property
    def symtype(self): return st.function
    def hassymtable(self): return True
    def getprefix(self): return 'function'

#class SymArray(Symbol):
#    pass

class SymType(Symbol):
    def istype(self): return True

    @property
    def symtype(self): return st.symtype
    def getprefix(self): return 'type'


class SymTypeAlias(SymType):
    def __init__(self, sname, target):
        super(SymTypeAlias, self).__init__(sname)
        self.target = target

    def __str__(self):
        name = super(SymTypeAlias, self).__str__()
        return '{0} (alias to "{1}")'.format(name, self.target)

class SymTypeArray(SymType):
    def __init__(self, basetype, range):
        self.format_string = 'array[{0}] of {1}'
        name = self.format_string.format(range, basetype)
        super(SymTypeArray, self).__init__(name)
        self.basetype, self.range = basetype, range
       
    @property
    def symtype(self): return st.array

class SymTypeRange(SymType):
    def __init__(self, leftbound, rightbound):
        self.format_string = '{0}..{1}'
        name = self.format_string.format(leftbound, rightbound)
        super(SymTypeRange, self).__init__(name)
        self.leftbound, self.rightbound = leftbound, rightbound

    def __str__(self):
        return self.getname()
        
    @property
    def symtype(self): return st.range
    def getprefix(self): return 'range'

class SymTypeRecord(SymType):
    def __init__(self, sname, types):
        SymType.__init__(self, sname)
        self.symtable = SymTable(types)

    @property
    def symtype(self): return st.record
    def hassymtable(self): return True

class SymTypeProcedure(SymType):
    @property
    def symtype(self): return st.procedure
    def hassymtable(self): return True
    def getprefix(self): return 'procedure'

class SymTypeFunction(SymTypeProcedure):
    @property
    def symtype(self): return st.function
    def getprefix(self): return 'function'

class SymTypeInt(SymType):
    def __init__(self): SymType.__init__(self, 'integer')
    @property
    def symtype(self): return st.integer

class SymTypeReal(SymType):
    def __init__(self): SymType.__init__(self, 'real')
    @property
    def symtype(self): return st.real

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
        return smb

    def write(self, shift=''):
        for symbolname, symboltype in sorted(self.items()):
            text = shift + '[' + symboltype.getprefix() + ']'
            if symboltype.istype():
                text = '{0} {1}'.format(text, symboltype)
            else:
                realtype = symboltype.gettype()
                text = '{0} {1}: {2!s}'.format(
                    text, symbolname, realtype.getname())
                if isinstance(symboltype, SymConst):
                    text = '{0} = {1}'.format(text, symboltype.getvalue())
                if realtype.hassymtable():
                    realtype.symtable.write(shift + '\t')
            print(text)
