# -*- coding: utf-8 -*-

from functions import *

class CompileError(Exception):
    @copy_args
    def __init__(self, message, linepos, *args):
        self.template = '{0} Error: {1}'
        self.message = message.format(*args)

    def __str__(self):
        l, p = self.linepos
        if p:
            self.linepos = '({0},{1})'.format(l, p)
        else:
            self.linepos = '({0})'.format(l)
        return self.template.format(self.linepos, self.message)

class LexError(CompileError): pass
class SynError(CompileError): pass

E_PAR_MISMATCH = 'Parenthesis mismatch'
E_RESERVED_NAME = 'Identifier \'{0}\' is reserved and not allowed for using'
E_CALL = 'Called object is neither a procedure nor a function'
E_REQUEST_FIELD = 'Request of field in something not a record'
E_SUBSCRIPT = 'Subscripted object is not an array'
E_UNDECLARED = 'Undeclared identifier \'{0}\''
E_REDECLARED = 'Redeclared identifier \'{0}\''
E_EXPECTED = "'{0}' expected but '{1}' found"
E_NOT_ALLOWED = "'{0}' not allowed"
E_INCOMPATIBLE_TYPES = "Incompatible types: expected '{0}' got '{1}'"
E_ORDINAL_EXPECTED = 'Ordinal expression expected'