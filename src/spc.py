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
-f, --full-syntax    perform a full parse
-g, --generate       generate assembly code\
'''

import sys
import os
import getopt
import subprocess
import StringIO

from version import APP_VERSION

from common.functions import *
from common.errors import CompileError
from tok.tokenizer import Tokenizer
from tok.printer import print_tokens
from syn.simple import SimpleParser
from syn.expressions import ExprParser
from syn.full import Parser
from syn.printer import SyntaxTreePrinter
from gen.main import Generator, FASM_PATH

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
        from tok.token import tt
        self._get_symbol_table(Parser)
        if self.parser.token.type == tt.kwBegin:
            self.parser.next_token()
            self._common_parse()
            self.parser.require_token(tt.kwEnd)
            self.parser.require_token(tt.dot)

    def parse(self):
        self.parser = Parser(self.tokenizer)
        program = self.parser.parse()
        self.parser.symtable.write()
        print ''
        program.display()

    def _get_symbol_table(self, ParserClass):
        self.parser = ParserClass(self.tokenizer)
        self.parser.parse_declarations()
        self.parser.symtable.write()

    def common_generate(self, optimize=False):
        self.parser = Parser(self.tokenizer)
        program = self.parser.parse()
        self.parser.check_program(program)
        self.generator = Generator(program, self.parser, optimize)
        return self.generator.generate()

    def generate(self):
        print self.common_generate()

    def optimize(self):
        self.compile_(optimize=True)

    def compile_(self, optimize=False):

        def check_code(process):
            if process.wait() > 0:
                raise CompileError('Assembling failed')

        fname = os.path.splitext(self.fname)[0]
        listing = fname + '.asm'
        with open(listing, 'w') as asmfile:
            asmfile.write(self.common_generate(optimize))
        if 'win' in sys.platform:
            fasm = os.path.join(FASM_PATH, 'fasm.exe')
            binary = fname + '.exe'
            check_code(
                subprocess.Popen('{0} {1} >nul'.format(
                    fasm, quote(listing)), shell=True))
        else:
            fasm = os.path.join(FASM_PATH, 'fasm')
            binary, output = fname + '.o', fname + '.exe'
            check_code(
                subprocess.Popen('{0} > /dev/null'.format(
                    ' '.join(map(quote, [fasm, listing, binary]))),
                    shell=True))
            subprocess.call(['gcc', binary, '-o' + output])
            os.remove(binary)
            subprocess.call(['strip', output])

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
        'decl':        Compiler.parse_decl,
        'full-syntax': Compiler.parse,
        'generate':    Compiler.generate,
        'optimize':    Compiler.optimize,
    }

    compiler_options = {'help' : 'h'}
    for key in compiler_actions:
        compiler_options[key] = key[0]
    compiler_actions['compile'] = Compiler.compile_

    try:
        opts, args = getopt.getopt(
            argv, ''.join(compiler_options.values()), compiler_options.keys())

        # [('-a', ''), ('--foo', '')] -> ['a', 'foo']
        opts = [o[0].lstrip('-') for o in opts]
    except getopt.GetoptError, e:
        return error('{0!s}, try --help for more options'.format(e))

    present = lambda o: o in opts or compiler_options[o] in opts

    if present('help') or len(opts) > 1:
        return usage()

    if not args:
        return error('no input files')
    for path in args:
        if not os.path.exists(path):
            return error('no such file or directory', path)
        if not os.path.isfile(path):
            return error('{0} is a directory, not a file'.format(path))

    if args and not opts:
        job = (('compile', arg) for arg in args)
    else:
        job = ((opt, arg) for arg in args for opt in compiler_options \
               if present(opt))
    try:
        for option, fname in job:
            with open(fname, buffering=10) as source:
                compiler_actions[option](Compiler(source, fname))
    except CompileError, e:
        return error(fname + str(e))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
