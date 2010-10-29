# -*- coding: utf-8 -*-

from UserDict import UserDict

from common.functions import copy_args

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

    @property
    def size(self):
        return self.type.size

    def is_local(self):
        return hasattr(self, 'local')

class SymConst(SymVar): pass

class SymFunctionArgument(SymVar):
    @copy_args
    def __init__(self, name, type, by_value, offset):
        self.value = None

class SymType(Symbol):
    def is_type(self): return True

class SymTypeFunction(SymType):
    @copy_args
    def __init__(self, name): pass

    @property
    def size(self):
        return 4 # call by offset

class SymTypeAlias(SymType):
    @copy_args
    def __init__(self, name, type): pass

    def __str__(self):
        return '{0} = {1}'.format(self.name, self.type.name)

    @property
    def size(self):
        return self.type.size

class SymTypeArray(SymType):
    @copy_args
    def __init__(self, type, range):
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return 'array[{0}] of {1}'.format(self.range, self.type.name)

    @property
    def size(self):
        return self.type.size * self.range.size

class SymTypeRange(SymType):
    @copy_args
    def __init__(self, leftbound, rightbound):
        SymType.__init__(self, self.__str__())

    def __str__(self):
        return '{0}..{1}'.format(self.leftbound, self.rightbound)

    @property
    def size(self):
        return self.rightbound - self.leftbound + 1


class SymTypeRecord(SymType):
    def __init__(self, name, table):
        self._symtable = table
        SymType.__init__(self, name)

    @property
    def symtable(self): return self._symtable

    @property
    def size(self):
        return sum(type_.size for type_ in self.symtable.values())

class SymTypeInt(SymType):
    def __init__(self):
        SymType.__init__(self, 'integer')
    @property
    def size(self):
        return 4

class SymTypeReal(SymType):
    def __init__(self):
        SymType.__init__(self, 'real')
    @property
    def size(self):
        return 4


class SimpleSymTable(UserDict):
    def clean_type(self, symtype):
        try:
            return symtype.text
        except AttributeError:
            return symtype

    def write(self):
        if not self:
            return
        print('Symbol table:')
        for sym, symtype in sorted(self.items()):
            print('{0}: {1}'.format(sym, self.clean_type(symtype)))

class SymTable(UserDict):
    def __init__(self):
        UserDict.__init__(self)
        self.current_offset = 0

    def insert(self, symbol):
        assert isinstance(symbol, Symbol)
        self.__setitem__(symbol.name, symbol)
        if isinstance(symbol, SymVar):
            symbol.offset = self.current_offset
            self.current_offset += symbol.size
        return symbol

    def iteritems(self):
        # avoid bug with iteration over UserDict (Python 2.6.4)
        return dict(self).iteritems()

    @property
    def size(self):
        return self.current_offset

    def write(self):
        self.write_symbols(self)
        self.write_functions()

    def write_symbols(self, table, shift=''):
        def writeln(text): print shift + str(text)
        writeln('::symtable begin::')
        table = sorted(table.iteritems())
        for name, symbol in table:
            if not isinstance(symbol, SymTypeFunction):
                writeln(symbol)
                while hasattr(symbol, 'type'):
                    symbol = symbol.type
                    if symbol.symtable and not hasattr(symbol, 'written'):
                        symbol.symtable.write_symbols(symbol.symtable, shift + '\t')
                    symbol.written = True
        writeln('::symtable end::')

    def write_functions(self):
        functions = sorted(
            [symbol for (name, symbol) in self.iteritems()
                if isinstance(symbol, SymTypeFunction)],
            key=lambda s: symbol.name)
        if functions:
            print '\n::functions::'
            for f in functions:
                type = 'function' if f.type else 'procedure'
                args = '; '.join(['{0}{1}: {2}'.format(
                    ('var ' if not arg.by_value else ''), arg.name, arg.type.name) for arg in f.args])
                print '{0} {1}({2})'.format(type, f.name, args) + \
                    (': {0};'.format(f.type.name) if f.type else '')
                if f.declarations:
                    self.write_symbols(f.declarations, ' ' * 2)
                f.body.display()

class SymTableStack(object):
    def __init__(self, table):
        self.content = []
        self.append(table)

    def append(self, table):
        self.content.append(table)

    def pop(self):
        return self.content.pop()

    def find(self, name):
        for table in self.tables:
            if isinstance(table, list):
                ntable = [symbol.name for symbol in table]
                if name in ntable:
                    return table[ntable.index(name)]
            if name in table:
                return table[name]
        return None

    @property
    def tables(self):
        return reversed(self.content)
    @property
    def current_table(self):
        return self.content[-1]
