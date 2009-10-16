# -*- coding: utf-8 -*-

class CompileError(BaseException):
    def __init__(self, filepos):
        self.line, self.pos = filepos

class LexError(CompileError):
    prefix = "Lexical error"
class BlockCommentEofError(LexError):
    message = "Unexpected end of file in block comment"
class StringEofError(LexError):
    message = "Unexpected end of file in string literal"

class SynError(CompileError):
    prefix = "Syntax error"
class UnexpectedTokenError(SynError):
    message = "Expected constant expression or identifier"
class ParMismatchError(SynError):
    message = "Parenthesis mismatch"

def raise_exception(e):
    template = "{0} on line {1}, col {2}. {3}"
    e.message = template.format(e.prefix, e.line, e.pos, e.message)
    raise e
