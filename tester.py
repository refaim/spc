# -*- coding: utf-8 -*-

import os
import sys
import shutil

from subprocess import Popen as popen, PIPE
from getopt import getopt, GetoptError

t_ext, a_ext, o_ext = ".in", ".a", ".o"

paths = ["tests/lexer/", "tests/expr/", "tests/plang/"]
binary_file_exts = {"-e": ".gif", "-d": ".gif"}
short_opts = "led"

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

        fout = open(test_path + fname + o_ext, "w")
        ferr = open(test_path + "tmp", "w")
        cmd = "{0} spc.py {1} {2}{3}"
        (out, err) = popen(args = cmd.format(
                               sys.executable, opt, test_path, entry),
                           stdout = fout, stderr = ferr,
                           shell = True, universal_newlines = True).communicate()
        ferr.close()
        ferr = open(test_path + "tmp", "r")
        for line in ferr.readlines():
            fout.write(line)
        ferr.close()
        os.remove(test_path + "tmp")
        fout.close()
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
