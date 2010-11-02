# -*- coding: utf-8 -*-

from common.functions import copy_args
from lib.enum import Enum

class Token(object):
    @copy_args
    def __init__(self, type=None, text='', value=''):
        self.line, self.pos = -1, -1

    @property
    def linepos(self):
        return self.line, self.pos

def prepare(prefix, seq):
    return [prefix + item.capitalize() for item in seq]

keywords = [
    'array', 
    'begin', 
    'break', 
    'const', 
    'continue', 
    'do', 
    'else',
    'end',
    'for', 
    'function', 
    'if', 
    'of',
    'procedure', 
    'record',
    'repeat',
    'result',
    'then',
    'to',
    'type',
    'until',
    'var',
    'while',
    'write',
    'writeln',
]

alphabetic = [
    'char_const', 
    'string_const', 
    'integer', 
    'boolean',
    'real',
    'identifier', 
    'eof',
]

special = {
    '.': 'dot',
    '+': 'plus', 
    '-': 'minus', 
    '*': 'mul',
    '/': 'div', 
    '=': 'equal', 
    '<': 'less',
    '>': 'greater',

    '<=': 'less_or_equal',
    '>=': 'greater_or_equal',
    ':=': 'assign',
    '<>': 'not_equal', 

    'and': 'logic_and', 
    'or':  'logic_or',
    'xor': 'logic_xor',
    'not': 'logic_not',
    'shr': 'shr',
    'shl': 'shl',
    'div': 'int_div',
    'mod': 'int_mod',

    ';':  'semicolon',
    ':':  'colon',
    ',':  'comma',
    '..': 'double_dot',
    '(':  'lparen',
    ')':  'rparen',
    '[':  'lbracket',
    ']':  'rbracket',
    '^':  'caret',
}
reverse_special = dict((v, k) for k, v in special.iteritems())

tt = Enum(*(prepare('kw', keywords) + alphabetic + special.values()))
del alphabetic
for token in tt:
    s = str(token)
    if s in reverse_special:
        token.text = reverse_special[s]
    if s.startswith('kw'):
        s = s.replace('kw', '', 1).lower()
        if s in keywords:
            token.text = s
