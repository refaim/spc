# -*- coding: utf-8 -*-

from functions import *

class CompileError(Exception):
    def __init__(self, filepos, params=[]):
        self.line, self.pos = filepos
        self.params = params


class LexError(CompileError):
    prefix = "Lexical error"

class IllegalCharError(LexError):
    message = "Illegal character '{0}'"
class CharConstError(LexError):
    message = "Invalid character constant"
class IntError(LexError):
    message = "Invalid integer constant"
class RealError(LexError):
    message = "Invalid real constant"
class BlockCommentEofError(LexError):
    message = "Unexpected end of file in block comment"
class StringEofError(LexError):
    message = "Unexpected end of file in string literal"


class SynError(CompileError):
    prefix = "Syntax error"

class NotYetImplementedError(SynError):
    message = '{0} are not yet implemented'
class ExpError(SynError):
    message = "'{0[0]}' expected but '{0[1]}' found"
class UnexpectedTokenError(SynError):
    message = "Unexpected character '{0}'"
class BracketsMismatchError(SynError):
    message = "Brackets mismatch"
class ParMismatchError(SynError):
    message = "Parenthesis mismatch"
class IdentifierExpError(SynError):
    message = "Identifier expected"
class UndeclaredIdentifierError(SynError):
    message = "Undeclared identifier '{0}'"
class RedeclaredIdentifierError(SynError):
    message = "Redeclared identifier '{0}'"
class ReservedNameError(SynError):
    message = "Identifier '{0}' is reserved and not allowed for using"
class VarInitError(SynError):
    message = "Only one variable can be initialized"
class UnknownTypeError(SynError):
    message = "Unknown type '{0}'"
class IncompatibleTypesError(SynError):
    message = "Incompatible types '{0[0]}' and '{0[1]}'"
class RangeBoundsError(SynError):
    message = "Upper bound of range is less than lower bound"
class CallError(SynError):
    message = "Called object is neither a procedure nor a function"
class SubscriptError(SynError):
    message = "Subscripted object is not an array"
class RecordError(SynError):
    message = "Request of field in something not a record"


def raise_exception(e):
    template = "{0} on line {1}, col {2}. {3}"
    if not empty(e.params):
        if len(e.params) == 1:
            e.params = first(e.params)
        e.message = e.message.format(e.params)
    e.message = template.format(e.prefix, e.line, e.pos, e.message)
    raise e
