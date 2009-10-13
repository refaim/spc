# -*- coding: utf-8 -*-

class SynNode: pass

class SynExpr(SynNode): pass

class SynBinaryOp(SynExpr):
    def __init__(self, opleft, optype, opright):
        self.optype = optype
        self.opleft, self.opright = opleft, opright

    def __str__(self):
        return "({0} {1} {2})".format(self.opleft, self.optype.text, self.opright)

class SynUnaryOp(SynExpr):
    def __init__(self, optype, operand):
        self.optype, self.operand = optype, operand

class SynConst(SynExpr):
    def __init__(self, const):
        self.token = const

    def __str__(self):
        return str(self.token.value)

class SynVar(SynExpr):
    def __init__(self, var):
        self.var = var

    def __str__(self):
        return self.var.text
