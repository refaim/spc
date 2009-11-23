
# -*- coding: utf-8 -*-

from sys import argv, stderr
from getopt import getopt, GetoptError

from tokenizer import Tokenizer
from synanalyzer import BasicParser, PseudoLangParser
from errors import CompileError
import tokenout
import synout

cname_s = "Small Pascal Compiler (by Roman Kharitonov)"
help_s = "usage: spc [OPTION]... [FILENAME]..."
try_s = "try 'spc --help' for more options"
empty_args_s = "no input files"
errmsg_s = "spc: {0}: {1}\n"

short_opts = "hled"
long_opts = ["help", "lex", "expr-parse", "expr-with-decl"]
opts_count = len(long_opts)
max_opt_len = max([len(opt) for opt in long_opts])
opts_descr = ["display this help text", "perform lexical analysis",
              "parse arithmetic expressions",
              "parse expressions with declarations in pseudolanguage"]

def help():
    print("{0}\n{1}\n".format(cname_s, help_s))
    for i in range(opts_count):
        space_count = max_opt_len - len(long_opts[i])
        print("-{0}, --{1}  {2}{3}".format(
            short_opts[i], long_opts[i], " " * space_count, opts_descr[i]))
    exit(0)

def common(args, action):
    if action == help: help()
    for arg in args:
        try:
            program = open(arg, "r", buffering = 1)
            tz = Tokenizer(program)
            action(tz, arg)
            program.close()
        except IOError as ioerr:
            stderr.write(errmsg_s.format(arg, ioerr.args[1]))
        except CompileError as cerr:
            stderr.write(errmsg_s.format(arg, cerr.message))
    if len(args) == 0:
        print(empty_args_s)

def lex(tokenizer, fname):
    tokens, error = tokenout.get_tokens(tokenizer)
    tokenout.print_tokens(tokens)
    if error: raise error

def common_parse(parser, fname):
    expressions, error = [], False
    try:
        e = parser.parse_expr()
        while e:
            expressions.append(e)
            e = parser.parse_expr()
    except CompileError as err:
        error = True
    printer = synout.SyntaxTreePrinter(expressions, fname)
    printer.write()
    if error:
        raise err

def e_parse(tokenizer, fname):
    common_parse(BasicParser(tokenizer), fname)

def ewd_parse(tokenizer, fname):
    parser = PseudoLangParser(tokenizer)
    parser.parse_decl()
    synout.print_symbol_table(parser.symtable)
    common_parse(parser, fname)

opts_actions = [help, lex, e_parse, ewd_parse]
try:
    opts, args = getopt(argv[1:], short_opts, long_opts)
    if len(opts) == 0: help()
    for option in opts:
        index = short_opts.index(option[0].lstrip('-')[0])
        common(args, opts_actions[index])
except GetoptError as opterr:
    print("{0}, {1}".format(opterr, try_s))
