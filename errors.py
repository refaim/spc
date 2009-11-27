# -*- coding: utf-8 -*-

class CompileError(BaseException):
    def __init__(self, filepos, params = []):
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
class FloatError(LexError):
    message = "Invalid float constant"
class BlockCommentEofError(LexError):
    message = "Unexpected end of file in block comment"
class StringEofError(LexError):
    message = "Unexpected end of file in string literal"

class SynError(CompileError):
    prefix = "Syntax error"
class UnexpectedTokenError(SynError):
    message = "Unexpected character '{0}'"
class IdentifierExpError(SynError):
    message = "Identifier expected"
class UndeclaredIdentifierError(SynError):
    message = "Undeclared identifier '{0}'"
class ReservedNameError(SynError):
    message = "Identifier '{0}' is reserved and not allowed for using"
class BracketsMismatchError(SynError):
    message = "Brackets mismatch"
class ParMismatchError(SynError):
    message = "Parenthesis mismatch"
class CallError(SynError):
    message = "Called object is neither a procedure nor a function"
class SubscriptError(SynError):
    message = "Subscripted object is neither an array nor a string"
class RecordError(SynError):
    message = "Request of field in something not a record"

def raise_exception(e):
    template = "{0} on line {1}, col {2}. {3}"
    if len(e.params) != 0:
        # создание кортежа из последовательности единичной длины
        # приводит к появлению запятой после элемента:
        # tuple([1]) == (1,)
        # tuple([1, 2, ..., n]) == (1, 2, ..., n)
        e.params = e.params[0] if len(e.params) == 1 else tuple(e.params)
        e.message = e.message.format(e.params)
    e.message = template.format(e.prefix, e.line, e.pos, e.message)
    raise e
