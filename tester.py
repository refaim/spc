#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-
# author: Roman Kharitonov refaim.vl@gmail.com

import sys, os, shutil
import glob, getopt

from common import *
from spc import main as run_compiler

class TestError(Exception):
    template = "Test #{0} {1}"
    def __init__(self, name):
        self.name = name

class Fail(TestError):
    message = "FAIL"
class NoAnswer(TestError):
    message = "NO ANSWER"

t_ext, a_ext, o_ext = ".in", ".a", ".o"

class Tester(object):
    def __init__(self, option, path):
        self.option, self.path = option, path
        self.suite = self.get_suite(path)
        self.passed, self.answer_present = True, True

    def get_suite(self, path):
        return sorted([t.replace('\\', '/') for t in glob.glob(path + '*' + t_ext)])

    def run(self):
        for entry in self.suite:
            self.testname = first(os.path.splitext(os.path.basename(entry)))
            self.test = self.path + self.testname
            self.run_test(entry)
            try:
                self.check()
            except TestError as result:
                print(result.template.format(result.name, result.message))
            else:
                print "Test #{0} OK".format(self.testname)

    def run_test(self, path):
        oldout = sys.stdout
        with open(self.test + o_ext, "w") as sys.stdout:
            run_compiler([self.option, path])
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
    ext = '.gif'
    def check(self):
        try:
            Tester.check(self)
        finally:
            output_present = os.path.exists(self.testname + self.ext)
            if output_present:
                shutil.move(self.testname + self.ext, self.test + o_ext + self.ext)
        answer_present = os.path.exists(self.test + a_ext + self.ext)
        self.answer_present = answer_present or not output_present
        self.passed = output_present or not answer_present
        if answer_present:
            self.compare(a_ext + self.ext, o_ext + self.ext, 'rb')

def error(msg):
    print(msg)
    return 2

def main(argv):
    optpaths = {'l': 'lexer',
                'e': 'expr',
                's': 'sdecl',
                'd': 'decl'}
    try:
        opts, args = getopt.getopt(argv, ''.join(optpaths.keys()))
    except getopt.GetoptError, e:
        return error(str(e) + ', use short variants of compiler options')
    if len(opts) > 1:
        return error('use only one option')
    if nonempty(args):
        return error('arguments are not allowed')

    option = first(first(opts))
    path = 'tests/{0}/'.format(optpaths[second(option)])
    tester_class = Tester if option == '-l' else DotTester
    tester = tester_class(option, path)
    tester.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
