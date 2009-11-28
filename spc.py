#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*- author: Roman Kharitonov refaim.vl@gmail.com

'''\
Small Pascal Compiler (by Roman Kharitonov)
Usage: spc [option] [filename1] [filename2] [...]

-h, --help           display this help text
-l, --lex            perform lexical analysis
-e, --expr           parse arithmetic expressions
-d, --decl-simple    parse expressions with simple declarations
'''

import sys, os
import getopt

from common import *
from tokenizer import Tokenizer
from synanalyzer import ExprParser, SimpleParser
from errors import CompileError
import tokenout, synout

class Compiler(object):
    def __init__(self, program, fname):
        self.tokenizer = Tokenizer(program)
        self.fname = fname

    def tokenize(self):
        tokens, error = tokenout.get_tokens(self.tokenizer)
        tokenout.print_tokens(tokens)
        if error: raise error

    def common_parse(self):
        expressions, fail = [], False
        try:
           e = self.parser.parse_expr()
           while e:
               expressions.append(e)
               e = self.parser.parse_expr()
        except CompileError as error:
            fail = True
        printer = synout.SyntaxTreePrinter(expressions, self.fname)
        printer.write()
        if fail: raise error

    def parse_expressions(self):
        self.parser = ExprParser(self.tokenizer)
        self.common_parse()

    def parse_simple_decl(self):
        self.parser = SimpleParser(self.tokenizer)
        self.parser.parse_decl()
        synout.print_symbol_table(self.parser.symtable)
        self.common_parse()

def usage():
    print __doc__
    return 0

def error(msg, fname = None):
    ''' Вывод сообщения об ошибке '''
    if fname:
        print('spc: {0}: {1}'.format(fname, msg))
    else:
        print('spc: {0}'.format(msg))
    return 2

def main(argv):
    # разбор опций командной строки
    # для корректной работы функции process() опция help должна быть первой в словаре
    option = {'help':        'h',
              'lex':         'l',
              'expr':        'e',
              'decl-simple': 'd'}
    try:
        opts, args = getopt.getopt(
            argv, ''.join(option.values()), option.keys())
    except getopt.GetoptError, e:
        return error(str(e) + ', try --help for more options')

    # обработка опций командной строки
    optuple = lambda o: ('-' + option[o], '--' + o) # 'opt' -> ('-o', '--opt')
    present = lambda o: some(first(opt) in optuple(o) for opt in opts)
    checkcomb = lambda lst: sum(int(present(opt) or False) for opt in lst) == 1

    if present('help') or empty(opts): return usage()
    if not checkcomb(option.keys()):
        return error('use only one of this options: ' +
                     ', '.join(first(opt) for opt in opts))

    if empty(args): return error('no input files')
    for path in args:
        if not os.path.exists(path):
            return error('no such file or directory', path)

    def process(opt, arg):
        with open(arg, 'r', buffering = 10) as source:
            worker = Compiler(source, arg)
            actions = [worker.tokenize,
                       worker.parse_expressions, worker.parse_simple_decl]
            actions[option.keys().index(opt)]()

    job = ((opt, arg) for arg in args for opt in option.keys() if present(opt))
    try:
        for opt, arg in job:
            process(opt, arg)
    except CompileError, e:
        return error(e.message, arg)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
