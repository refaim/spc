# -*- coding: utf-8 -*-

from common.functions import copy_args
from tok.token import Token, tt

class SynNode(object):
    def indent(self, depth, string): return ' ' * depth + string
    def deeper(self, depth): return depth + 2

class SynStatement(SynNode): pass

class SynEmptyStatement(SynNode):
    def display(self, depth):
        print self.indent(depth, ';')

class SynStatementBlock(SynStatement):
    @copy_args
    def __init__(self, statements=[]): pass
    def add(self, statement): self.statements.append(statement)
    def display(self, depth=0):
        print self.indent(depth, 'begin')
        for statement in self.statements:
            statement.display(self.deeper(depth))
        print self.indent(depth, 'end')

class SynStatementFor(SynStatement):
    @copy_args
    def __init__(self, counter, initial, final, action):
        self.assignment = SynOperation(
            Token(tt.assign), counter, initial)
        self.check = SynOperation(
            Token(tt.less_or_equal), counter, final)

    def display(self, depth):
        print self.indent(depth, 'for {0} := {1} to {2} do'.format(
            self.counter, self.initial, self.final))
        self.action.display(self.deeper(depth))

class SynStatementWhile(SynStatement):
    @copy_args
    def __init__(self, condition, action): pass
    def display(self, depth):
        print self.indent(depth, 'while {0} do'.format(self.condition))
        self.action.display(self.deeper(depth))

class SynStatementRepeat(SynStatement):
    @copy_args
    def __init__(self, condition, action): pass
    def display(self, depth):
        print self.indent(depth, 'repeat')
        self.action.display(self.deeper(depth))
        print self.indent(depth, 'until {0}'.format(self.condition))

class SynStatementIf(SynStatement):
    @copy_args
    def __init__(self, condition, action, else_action): pass
    def display(self, depth):
        print self.indent(depth, 'if {0} then'.format(self.condition))
        self.action.display(self.deeper(depth))
        if self.else_action:
            print self.indent(depth, 'else')
            self.else_action.display(self.deeper(depth))

class SynStatementBreak(SynStatement):
    def display(self, depth):
        print self.indent(depth, 'break')

class SynStatementContinue(SynStatement):
    def display(self, depth):
        print self.indent(depth, 'continue')

class SynStatementWrite(SynStatement):
    @copy_args
    def __init__(self, newline, *args):
        self.args = args
    def display(self, depth):
        name = 'writeln' if self.newline else 'write'
        print self.indent(depth, '{0}({1})'.format(
            name, ', '.join(map(str, self.args))))

class SynStatementResult(SynStatement):
    @copy_args
    def __init__(self, value, type_): pass
    def display(self, depth):
        print self.indent(depth, 'result := {0!s}'.format(self.value))

class SynExpr(SynNode):
    def display(self, depth): print self.indent(depth, self.__str__())
    @property
    def children(self): return []

class SynCastToReal(SynExpr):
    @copy_args
    def __init__(self, expression): pass
    def type_(self, stack):
        return stack.find('real')

class SynCall(SynExpr):
    @copy_args
    def __init__(self, caller, args=[]): pass
    def __str__(self): return '{0}({1})'.format(
        self.caller, ', '.join(str(arg) for arg in self.args))
    def type_(self, stack):
        return self.caller.type_(stack)

    @property
    def label(self): return '()'
    @property
    def children(self): return [self.caller] + self.args

class SynSubscript(SynExpr):
    @copy_args
    def __init__(self, array, index): pass
    def __str__(self): return '{0}[{1}]'.format(self.array, self.index)
    def type_(self, stack):
        arrtype = self.array.type_(stack).type
        if hasattr(arrtype, 'type'):
            arrtype = arrtype.type
        return arrtype
    @property
    def name(self): return self.array.name

class SynFieldRequest(SynExpr):
    @copy_args
    def __init__(self, record, field): pass
    def __str__(self): return '{0}.{1}'.format(self.record, self.field)
    def type_(self, stack):
        rectype = self.record.type_(stack)
        if hasattr(rectype, 'type'):
            rectype = rectype.type
        stack.append(rectype.symtable)
        result = self.field.type_(stack)
        stack.pop()
        return result

class SynOperation(SynExpr):
    @copy_args
    def __init__(self, operation, *operands):
        self.operands = list(operands)
    def __str__(self):
        if len(self.operands) == 1:
            op = self.operation.text
            if op == 'not':
                op += ' '
            text = op + str(self.operands[0])
        else:
            text = '{0[0]} {1} {0[1]}'.format(
                self.operands, self.operation.text)
        return '(' + text + ')'
    def type_(self, stack):
        # this function used only in code generator
        # for getting param size
        return stack.find('integer')

    @property
    def label(self):
        text = self.operation.text
        return text if text != '[' else '[]'
    @property
    def pos(self): return self.operation.linepos
    @property
    def children(self): return self.operands

class SynVar(SynExpr):
    @copy_args
    def __init__(self, token): pass
    def __str__(self): return str(self.name)
    @property
    def label(self): return self.token.text
    @property
    def name(self): return self.token.value
    @property
    def pos(self): return self.token.linepos
    def type_(self, stack): return stack.find(self.name)

class SynConst(SynVar):
    def type_(self, stack): return stack.find(str(self.token.type))
