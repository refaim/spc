# -*- coding: utf-8 -*-

from common.functions import *
    
class SynNode(object): pass

class SynStatement(SynNode):
    def is_loop(self): return False

class SynStatementFor(SynStatement):
    @copy_args
    def __init__(self, counter, initial, final, statement): pass
    def is_loop(self): return True

class SynStatementWhile(SynStatement):
    @copy_args
    def __init__(self, condtition, action): pass
    def is_loop(self): return True

class SynStatementIf(SynStatement):
    @copy_args
    def __init__(self, condtition, action, else_action): pass


class SynExpr(SynNode):
    @property
    def children(self): return []

class SynOperation(SynExpr):
    @copy_args
    def __init__(self, operation, operands):
        if not isinstance(operands, list):
            self.operands = [operands]

    def __str__(self):
        text = self.operation.text
        return text if text != "[" else "[]"

    @property
    def children(self): return self.operands

class SynFunctionCall(SynExpr):
    @copy_args
    def __init__(self, func, args=[]): pass

    def __str__(self):
        return "()"

    @property
    def children(self): return [self.func] + self.args

class SynVar(SynExpr):
    @copy_args
    def __init__(self, token): pass

    def __str__(self):
        return self.token.text

class SynConst(SynVar): pass
