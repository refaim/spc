# -*- coding: utf-8 -*-

import os
from subprocess import Popen as popen
from getopt import getopt
from sys import argv

t_ext, a_ext, o_ext = ".in", ".a", ".o"

opts, args = getopt(argv[1:], "le")
opt = opts[0][0]
if opt == "-l":
    test_path = "tests\\lexer\\"
elif opt == "-e":
    test_path = "tests\\parser\\"
else:
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
        
        print(msg + "OK") if fout.read() == fans.read() else print(msg + "FAIL")
        
        fout.close() 
        fans.close()
