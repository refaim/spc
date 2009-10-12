# -*- coding: utf-8 -*-

class SynNode: pass

class SynExpr(SynNode): pass

class SynBinaryOp(SynExpr):
    def __init__(self, left_op, optype, right_op):
        self.optype = optype                    
        self.left_op, self.right_op = left_op, right_op

    def __str__(self):
        return "({0} {1} {2})".format(self.left_op, self.optype, self.right_op)

class SynUnaryOp(SynExpr):
    def __init__(self, optype, operand):
        self.optype, self.operand = optype, operand

class SynConst(SynExpr):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class SynVar(SynExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
