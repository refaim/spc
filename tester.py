# -*- coding: utf-8 -*-

import os
from subprocess import Popen as popen

test_path = "tests\\lexer\\"
t_ext = ".in"
a_ext = ".a"
o_ext = ".o"

test_dir = os.walk(test_path)
for root, dirs, files in test_dir:
    for entry in files:
        fname, ext = os.path.splitext(entry)
        if ext.lower() != t_ext: continue

        fout = open(test_path + fname + o_ext, "w")
        app = popen(args = "python spc.py --lex {0}{1}".format(test_path, entry), 
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
