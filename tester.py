# -*- coding: utf-8 -*-

import os
from subprocess import Popen as popen
from getopt import getopt, GetoptError
from sys import argv

t_ext, a_ext, o_ext = ".in", ".a", ".o"

short_opts = "le"
paths = ["tests\\lexer\\", "tests\\parser\\"]

try:
    opts, args = getopt(argv[1:], short_opts)
    opt = opts[0][0]
    index = short_opts.index(opt.lstrip('-'))
    test_path = paths[index]
except GetoptError as opterr:
    print("{0}, {1}".format(opterr, "use short variants of compiler options"))
    exit()

test_dir = os.walk(test_path)
for root, dirs, files in test_dir:
    for entry in files:
        fname, ext = os.path.splitext(entry)
        if ext.lower() != t_ext: continue

        fout = open(test_path + fname + o_ext, "w")
        app = popen(args = "python spc.py {0} {1}{2}".format(opt, test_path, entry),
                    stdout = fout).communicate()
        fout.close()
        msg = "Test #{0} ".format(fname)
        try:
            fans = open(test_path + fname + a_ext, "r")
            fout = open(test_path + fname + o_ext, "r")
        except IOError:
            print(msg + "NO ANSWER")
            continue
        
        print(msg + "OK") if fout.read() == fans.read() else (msg + "FAIL")
        
        fout.close() 
        fans.close()
