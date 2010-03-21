# -*- coding: utf-8 -*-

# py2exe setup script

from distutils.core import setup
import py2exe

setup(
    name = 'Small Pascal Compiler',
    author = 'Roman Kharitonov',
    author_email = 'refaim.vl@gmail.com',
    url = 'http://github.com/refaim/spc',
    console = ['spc.py', 'tester.py'])
