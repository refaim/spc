# -*- coding: utf-8 -*-

import os
import sys
from subprocess import Popen as popen, PIPE
from getopt import getopt, GetoptError

t_ext, a_ext, o_ext = ".in", ".a", ".o"

paths = ["tests/lexer/", "tests/expr/", "tests/plang/"]

short_opts = "led"
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
        
        fout = open(test_path + fname + o_ext, "w")
        cmd = "{0} spc.py {1} {2}{3}"
        (out, err) = popen(args = cmd.format(sys.executable, opt, test_path, entry),
                           stdout = fout, #stderr = PIPE, 
                           shell = True, universal_newlines = True).communicate()
        fout.close()
        msg = "Test #{0} ".format(fname)
        try:
            fans = open(test_path + fname + a_ext, "rU")
            fout = open(test_path + fname + o_ext, "rU")
        except IOError:
            print(msg + "NO ANSWER")
            continue
        
        print(msg + "OK") if fout.read() == fans.read() else (msg + "FAIL")
        if err: 
            print(err)
            exit(1)
                    
        fout.close() 
        fans.close()
