#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import shutil
import glob
import getopt
import subprocess

import dot_parser

from common.errors import CompileError
from common.functions import copy_args
from spc import main as run_compiler

class TestError(Exception):
    template = "Test #{0} {1}"

    @copy_args
    def __init__(self, name): pass
    def __str__(self):
        return self.template.format(self.name, self.result)

class Fail(TestError):
    result = "FAIL"
class NoAnswer(TestError):
    result = "NO ANSWER"

class AdvancedFail(Fail):
    @copy_args
    def __init__(self, name, message):
        super(AdvancedFail, self).__init__(name)
    def __str__(self):
        return '{0}\n{1}'.format(
            super(AdvancedFail, self).__str__(), self.message)

t_ext, a_ext, o_ext = ".tst", ".ans", ".out"

class Tester(object):
    @copy_args
    def __init__(self, option, path, verbose, full=False):
        self.suite = self.get_suite()
        self.passed, self.answer_present = True, True

    def get_suite(self):
        return sorted(test.replace('\\', '/') for test in
            glob.glob(os.path.join(self.path, '*' + t_ext)))

    def run(self):
        for entry in self.suite:
            self.testname = os.path.splitext(os.path.basename(entry))[0]
            self.test = os.path.normpath(os.path.join(self.path, self.testname))
            self.run_test(entry)
            try:
                self.check()
            except TestError as result:
                print(str(result))
                if not self.full:
                    return (1, len(self.suite))
            else:
                if self.verbose:
                    print "Test #{0} OK".format(self.testname)
        return (0, len(self.suite))

    def run_test(self, path):
        argv = ([self.option] if self.option else []) + [path]
        oldout = sys.stdout
        try:
            with open(self.test + o_ext, "w") as sys.stdout:
                run_compiler(argv)
        except CompileError as e:
            raise e
        finally:
            sys.stdout = oldout

    def compare(self, first, second, mode):
        with open(self.test + first, mode) as answer:
            with open(self.test + second, mode) as output:
                self.passed = output.read() == answer.read()

    def check(self):
        self.answer_present = os.path.exists(self.test + a_ext)
        self.compare(a_ext, o_ext, 'rU')

    def set_passed(self, value):
        if not value:
            raise Fail(self.testname)

    def set_answer_present(self, value):
        if not value:
            raise NoAnswer(self.testname)

    passed = property(fset = set_passed)
    answer_present = property(fset = set_answer_present)

class DotTester(Tester):
    ext = '.dot'
    hr_ext = '.gif' # human-readable format
    def check(self):
        try:
            Tester.check(self)
        finally:
            output_present = os.path.exists(self.testname + self.ext)
            if output_present:
                shutil.move(self.testname + self.ext,
                    self.test + o_ext + self.ext)
                shutil.move(self.testname + self.hr_ext,
                    self.test + o_ext + self.hr_ext)
        answer_present = os.path.exists(self.test + a_ext + self.ext)
        self.answer_present = answer_present or not output_present
        self.passed = output_present or not answer_present
        if answer_present:
            self.compare_dot(a_ext + self.ext, o_ext + self.ext, 'rb')

    def compare_dot(self, first, second, mode):
        def nodes(g):
            subgraphs = []
            for subgraph in g.get_subgraph_list():
                subgraphs.append(
                    [(node.get_name(), node.get_label())
                        for node in subgraph.get_node_list()])
            return subgraphs

        def edges(g):
            subgraphs = []
            for subgraph in g.get_subgraph_list():
                subgraphs.append(
                    [(edge.get_source(), edge.get_destination())
                        for edge in subgraph.get_edge_list()])
            return subgraphs

        with open(self.test + first, mode) as answer:
            with open(self.test + second, mode) as output:
                agraph = dot_parser.parse_dot_data(answer.read())
                ograph = dot_parser.parse_dot_data(output.read())
                return nodes(agraph) == nodes(ograph) and \
                       edges(agraph) == edges(ograph)

class ExecutableTester(Tester):
    def check(self):
        exe = self.test + '.exe'
        if not os.path.exists(exe):
            raise AdvancedFail(self.testname, 'Executable not found')
        with open(self.test + o_ext, 'w') as out:
            subprocess.Popen(exe, shell=True, stdout=out).wait()
        super(ExecutableTester, self).check()

def error(msg):
    print(msg)
    return 2

def main(argv):
    optpaths = {
        'l': 'lexer',
        'e': 'expr',
        's': 'sdecl',
        'd': 'decl',
        'f': 'full',
        '' : 'gen',
    }

    names = {
        'l': 'Tokenizer',
        'e': 'Expressions parser',
        's': 'Simple declarations parser',
        'd': 'Declarations parser',
        'f': 'Full syntax parser',
    }
    priorities = 'lesdf'

    try:
        opts, args = getopt.getopt(argv, ''.join(optpaths.keys()) + 'avu')
    except getopt.GetoptError, e:
        return error(str(e) + ', use short variants of compiler options')
    opts = [o[0].lstrip('-') for o in opts]
    if args:
        return error('arguments are not allowed')
    if 'v' in opts:
        verbose = True
        opts.pop(opts.index('v'))
    else:
        verbose = False
    if 'u' in opts:
        full = True
        opts.pop(opts.index('u'))
    else:
        full = False
    if len(opts) > 1:
        return error('use only one option')
    option = opts[0] if opts else ''

    if option == 'a':
        for opt in priorities:
            print '{0}...'.format(names[opt])
            args = ['-' + opt]
            if verbose:
                args.append('-v')
            if full:
                args.append('-f')
            code, count = main(args)
            if code != 0:
                return code
            print '{0} tests ok'.format(count)
        return 0

    path = 'tests/{0}/'.format(optpaths[option])
    if option in ('l', 'f'):
        tester_class = Tester
    elif option in ('s', 'd', 'e'):
        tester_class = DotTester
    else:
        tester_class = ExecutableTester
    tester = tester_class(('-' + option) if option else '', path, verbose, full)
    return tester.run()

if __name__ == '__main__':
    try:
        retcode = main(sys.argv[1:])
        if isinstance(retcode, tuple):
            sys.exit(retcode[0])
        else:
            sys.exit(retcode)
    except KeyboardInterrupt:
        print "Interrupted by user"
