#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Roman Kharitonov, refaim.vl@gmail.com

'''\
Small Pascal Compiler v{version} (by Roman Kharitonov)
Usage: spc [option] [filename1] [filename2] [...]

-h, --help           display this help text
-l, --lex            perform lexical analysis
-e, --expr           parse arithmetic expressions
-s, --simple-decl    parse expressions with simple declarations
-d, --decl           parse normal Pascal declarations
-f, --full-syntax    perform a full parse\
'''

import sys
import os
import getopt

from version import APP_VERSION

from common.functions import *
from common.errors import CompileError
from tok.tokenizer import Tokenizer
from tok.printer import print_tokens
from syn.simple import SimpleParser
from syn.expressions import ExprParser
from syn.full import Parser
from syn.printer import SyntaxTreePrinter

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

    def parse_declarations(self):
        self._get_symbol_table(Parser)
        self._common_parse()

    def parse(self):
        self.parser = Parser(self.tokenizer)
        self.parser.parse()
        self.parser.symtable.write()
        self._common_parse()

    def _get_symbol_table(self, ParserClass):
        self.parser = ParserClass(self.tokenizer)
        self.parser.parse_declarations()
        self.parser.symtable.write()

def usage():
    print(__doc__.format(version=APP_VERSION))
    return 0

def error(msg, fname=None):
    if fname is not None:
        print('spc: {0}: {1}'.format(fname, msg))
    else:
        print('spc: {0}'.format(msg))
    return 2

def main(argv):
    compiler_actions = { 
        'lex':         Compiler.tokenize,
        'expr':        Compiler.parse_expressions,
        'simple-decl': Compiler.parse_simple_decl,
        'decl':        Compiler.parse_declarations,
        'full-syntax': Compiler.parse,
    }

    compiler_options = {'help' : 'h'}
    for key in compiler_actions:
        compiler_options[key] = first(key)

    try:
        opts, args = getopt.getopt(
            argv, ''.join(compiler_options.values()), compiler_options.keys())

        # [('-a', ''), ('--foo', '')] -> ['a', 'foo']
        opts = [first(o).lstrip('-') for o in opts]
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
