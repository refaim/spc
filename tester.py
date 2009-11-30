#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*- author: Roman Kharitonov refaim.vl@gmail.com

import sys, os, shutil
from getopt import getopt, GetoptError

from common import *
from spc import main as run_compiler

t_ext, a_ext, o_ext = ".in", ".a", ".o"

paths = ["tests/lexer/", "tests/expr/", "tests/plang/"]
binary_file_exts = {"-e": ".gif", "-s": ".gif"}
short_opts = "les"

def has_binary_output(option):
    return option in binary_file_exts

try:
    opts, args = getopt(sys.argv[1:], short_opts)
    opt = opts[0][0]
    index = short_opts.index(opt.lstrip('-'))
    test_path = paths[index]
except GetoptError as opterr:
    print("{0}, {1}".format(opterr, "use short variants of compiler options"))
    exit()

test_dir = os.walk(test_path)
for root, dirs, files in test_dir:
    files.sort()
    for entry in files:
        fname, ext = os.path.splitext(entry)
        if ext != t_ext: continue

        old = sys.stdout
        with open(test_path + fname + o_ext, "w") as sys.stdout:
            run_compiler([opt, test_path + entry])
        sys.stdout = old

        msg = "Test #{0} ".format(fname)
        passed, answer_present = True, True

        if has_binary_output(opt):
            b_ext = binary_file_exts[opt]
            b_path = fname + b_ext
            if os.path.exists(b_path):
                shutil.move(b_path, test_path + fname + o_ext + b_ext)

            b_path = "{0}{1}{2}".format(test_path + fname, "{0}", b_ext)
            bans_path, bout_path = b_path.format(a_ext), b_path.format(o_ext)
            exa, exo = os.path.exists(bans_path), os.path.exists(bout_path)
            if exa == exo == True:
                bans = open(bans_path, "rb")
                bout = open(bout_path, "rb")
                passed = bans.read() == bout.read()
                bans.close()
                bout.close()
            else:
                if exa and not exo:
                    passed = False
                elif exo and not exa:
                    answer_present = False

        answer_present = answer_present and os.path.exists(test_path + fname + a_ext)
        if not answer_present:
            print(msg + "NO ANSWER")
            continue

        fans = open(test_path + fname + a_ext, "rU")
        fout = open(test_path + fname + o_ext, "rU")
        passed = passed and fout.read() == fans.read()
        print(msg + "OK") if passed else (msg + "FAIL")
        #if err:
        #    print(err)
        #    exit(1)

        fout.close()
        fans.close()
