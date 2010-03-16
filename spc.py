#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-
# author: Roman Kharitonov refaim.vl@gmail.com

'''\
Small Pascal Compiler (by Roman Kharitonov)
Usage: spc [option] [filename1] [filename2] [...]

-h, --help           display this help text
-l, --lex            perform lexical analysis
-e, --expr           parse arithmetic expressions
-s, --simple-decl    parse expressions with simple declarations
-d, --decl           parse normal Pascal declarations\
'''

import sys
import os
import getopt

from common import *
from errors import CompileError
from tokenizer import Tokenizer
import tokenout
from simplesynanalyzer import SimpleParser
from synanalyzer import ExprParser, Parser
from synout import SyntaxTreePrinter

class Compiler(object):
    def __init__(self, program, fname):
        self.tokenizer = Tokenizer(program)
        self.fname = fname

    def tokenize(self):
        tokens = []
        try:
            for token in self.tokenizer:
                tokens.append(token)
        finally:
            tokenout.print_tokens(tokens)

    def common_parse(self):
        expressions = []
        try:
            for expr in self.parser:
                expressions.append(expr)
        finally:
            SyntaxTreePrinter(expressions, self.fname).write()

    def parse_expressions(self):
        self.parser = ExprParser(self.tokenizer)
        self.common_parse()

    def get_symbol_table(self, ParserClass):
        self.parser = ParserClass(self.tokenizer)
        self.parser.parse_decl()
        self.parser.symtable.write()

    def parse_simple_decl(self):
        self.get_symbol_table(SimpleParser)
        self.common_parse()

    def parse_decl(self):
        self.get_symbol_table(Parser)

def usage():
    print(__doc__)
    return 0

def error(msg, fname = None):
    ''' Вывод сообщения об ошибке '''
    if fname is not None:
        print('spc: {0}: {1}'.format(fname, msg))
    else:
        print('spc: {0}'.format(msg))
    return 2

def main(argv):
    # разбор опций командной строки
    option = {'help':        'h',
              'lex':         'l',
              'expr':        'e',
              'simple-decl': 's',
              'decl':        'd'}
    try:
        opts, args = getopt.getopt(
            argv, ''.join(option.values()), option.keys())
    except getopt.GetoptError, e:
        return error(str(e) + ', try --help for more options')

    # обработка опций командной строки
    optuple = lambda o: ('-' + option[o], '--' + o) # 'opt' -> ('-o', '--opt')
    present = lambda o: some(first(opt) in optuple(o) for opt in opts)
    # проверка на наличие нескольких опций, пишущих в файлы/stdout
    opcheck = lambda lst: sum(int(present(opt) or False) for opt in lst) == 1

    if present('help') or empty(opts):
        return usage()
    if not opcheck(option.keys()):
        return error('use only one of this options: ' +
                     ', '.join(first(opt) for opt in opts))

    if empty(args):
        return error('no input files')
    for path in args:
        if not os.path.exists(path):
            return error('no such file or directory', path)
        if not os.path.isfile(path):
            return error('{0} is a directory, not a file'.format(path))

    def process(opt, arg):
        with open(arg, 'r', buffering = 10) as source:
            c = Compiler(source, arg)
            action = { 'lex':         c.tokenize,
                       'expr':        c.parse_expressions,
                       'simple-decl': c.parse_simple_decl,
                       'decl':        c.parse_decl         }
            action[opt]()

    job = ((opt, arg) for arg in args for opt in option.keys() if present(opt))
    try:
        for opt, arg in job:
            process(opt, arg)
    except CompileError, e:
        return error(e.message, arg)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
