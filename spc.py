#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Roman Kharitonov, refaim.vl@gmail.com

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
from simplesynanalyzer import SimpleParser
from synanalyzer import ExprParser, Parser

from tokenout import print_tokens
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
            print_tokens(tokens)

    def _common_parse(self):
        expressions = []
        try:
            for expr in self.parser:
                expressions.append(expr)
        finally:
            SyntaxTreePrinter(expressions, self.fname).write()

    def parse_expressions(self):
        self.parser = ExprParser(self.tokenizer)
        self._common_parse()

    def parse_simple_decl(self):
        self._get_symbol_table(SimpleParser)
        self._common_parse()

    def parse_decl(self):
        self._get_symbol_table(Parser)

    def _get_symbol_table(self, ParserClass):
        self.parser = ParserClass(self.tokenizer)
        self.parser.parse_decl()
        self.parser.symtable.write()

def usage():
    print(__doc__)
    return 0

def error(msg, fname=None):
    if fname is not None:
        print('spc: {0}: {1}'.format(fname, msg))
    else:
        print('spc: {0}'.format(msg))
    return 2

def main(argv):
    compiler_actions = { 'lex':         Compiler.tokenize,
                         'expr':        Compiler.parse_expressions,
                         'simple-decl': Compiler.parse_simple_decl,
                         'decl':        Compiler.parse_decl         }

    compiler_options = {'help' : 'h'}
    for key in compiler_actions:
        compiler_options[key] = first(key)

    try:
        opts, args = getopt.getopt(
            argv, ''.join(compiler_options.values()), compiler_options.keys())

        # [('-a', ''), ('--foo', '')] -> ['a', 'foo']
        opts = map(lambda o: first(o).lstrip('-'), opts)
    except getopt.GetoptError, e:
        return error('{0!s}, try --help for more options'.format(e))

    present = lambda o: o in opts or compiler_options[o] in opts

    if present('help') or empty(opts) or len(opts) > 1:
        return usage()

    if empty(args):
        return error('no input files')
    for path in args:
        if not os.path.exists(path):
            return error('no such file or directory', path)
        if not os.path.isfile(path):
            return error('{0} is a directory, not a file'.format(path))

    job = ((opt, arg) for arg in args for opt in compiler_options if present(opt))
    try:
        for option, fname in job:
            with open(fname, buffering=10) as source:
                compiler_actions[option](Compiler(source, fname))
    except CompileError, e:
        return error(e.message, fname)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
