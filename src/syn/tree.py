# -*- coding: utf-8 -*-

from common.functions import *
    
class SynNode(object):
    def indent(self, deep, string): return ' ' * deep + string
    def go_deeper(self, deep): return deep + 2

class SynStatement(SynNode): pass

class SynEmptyStatement(SynNode):
    def display(self, deep):
        print self.indent(deep, ';')

class SynStatementBlock(SynStatement):
    @copy_args
    def __init__(self, statements=[]): pass
    def add(self, statement): self.statements.append(statement)
    def display(self, deep=0):
        print self.indent(deep, 'begin')
        for statement in self.statements:
            statement.display(self.go_deeper(deep))
        print self.indent(deep, 'end')

class SynStatementFor(SynStatement):
    @copy_args
    def __init__(self, counter, initial, final, action): pass
    def display(self, deep):
        print self.indent(deep, 'for {0} := {1} to {2} do'.format(
            self.counter, self.initial, self.final))
        self.action.display(self.go_deeper(deep))

class SynStatementWhile(SynStatement):
    @copy_args
    def __init__(self, condtition, action): pass
    def display(self, deep):
        print self.indent(deep, 'while {0} do'.format(self.condtition))
        self.action.display(self.go_deeper(deep))

class SynStatementIf(SynStatement):
    @copy_args
    def __init__(self, condtition, action, else_action): pass
    def display(self, deep):
        print self.indent(deep, 'if {0} then'.format(self.condtition))
        self.action.display(self.go_deeper(deep))
        if self.else_action:
            print self.indent(deep, 'else')
            self.else_action.display(self.go_deeper(deep))

class SynStatementBreak(SynStatement):
    def display(self, deep):
        print self.indent(deep, 'break')

class SynStatementContinue(SynStatement):
    def display(self, deep):
        print self.indent(deep, 'continue')

class SynExpr(SynNode):
    def display(self, deep): print self.indent(deep, self.__str__())
    @property
    def children(self): return []
    @property
    def type(self, table): return None

class SynCall(SynExpr):
    @copy_args
    def __init__(self, caller, args=[]): pass
    def __str__(self): return '{0}({1})'.format(
        self.caller, ' '.join(args))
    @property
    def label(self): return '()'

    @property
    def children(self): return [self.caller] + self.args

class SynSubscript(SynExpr):
    @copy_args
    def __init__(self, array, index): pass
    def __str__(self): return '{0}[{1}]'.format(self.array, self.index)

class SynFieldRequest(SynExpr):
    @copy_args
    def __init__(self, record, field): pass
    def __str__(self): return '{0}.{1}'.format(self.record, self.field)

class SynOperation(SynExpr):
    @copy_args
    def __init__(self, operation, *operands):
        self.operands = operands
    def __str__(self):
        if len(self.operands) == 1:
            return self.operation.text + str(self.operands[0])
        else:
            return '{0} {1} {2}'.format(
                self.operands[0], self.operation.text, self.operands[1])
    @property
    def label(self):
        text = self.operation.text
        return text if text != '[' else '[]'

    @property
    def children(self): return self.operands

class SynVar(SynExpr):
    @copy_args
    def __init__(self, token): pass
    def __str__(self): return str(self.token.value)
    @property
    def label(self): return self.token.text

    @property
    def type(self, table): return table[self.token.value].type

class SynConst(SynVar): pass
