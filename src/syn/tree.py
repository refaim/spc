# -*- coding: utf-8 -*-

from common.functions import *
    
class SynNode(object): pass

class SynExpr(SynNode):
    def get_children(self):
        return []

class SynUnaryOp(SynExpr):
    @copy_args
    def __init__(self, optype, operand): pass

    def __str__(self):
        return self.optype.text

    def get_children(self):
        return [self.operand]

class SynBinaryOp(SynExpr):
    @copy_args
    def __init__(self, opleft, optype, opright): pass

    def __str__(self):
        text = self.optype.text
        return text if text != "[" else "[]"

    def get_children(self):
        return [self.opleft, self.opright]

class SynFunctionCall(SynExpr):
    @copy_args
    def __init__(self, func, args=[]): pass

    def __str__(self):
        return "()"

    def get_children(self):
        return [self.func] + self.args

class SynVar(SynExpr):
    @copy_args
    def __init__(self, token): pass

    def __str__(self):
        return self.token.text

class SynConst(SynVar):
    pass
