# -*- coding: utf-8 -*-

class SynNode: pass

class SynExpr(SynNode):
    def get_children(self):
        return []

class SynUnaryOp(SynExpr):
    def __init__(self, optype, operand):
        self.optype, self.operand = optype, operand

    def __str__(self):
        return self.optype.text

    def get_children(self):
        return [self.operand]

class SynBinaryOp(SynExpr):
    def __init__(self, opleft, optype, opright):
        self.optype, self.opleft, self.opright = optype, opleft, opright

    def __str__(self):
        text = self.optype.text
        return text if text != "[" else "[]"

    def get_children(self):
        return [self.opleft, self.opright]

class SynDotOp(SynBinaryOp):
    pass

class SynFunctionCall(SynExpr):
    def __init__(self, func, args = []):
        self.func, self.args = func, args

    def __str__(self):
        return "()"

    def get_children(self):
        return [self.func] + self.args

class SynVar(SynExpr):
    def __init__(self, var):
        self.var = var

    def __str__(self):
        return self.var.text

class SynConst(SynExpr):
    def __init__(self, const):
        self.token = const

    def __str__(self):
        return self.token.text
