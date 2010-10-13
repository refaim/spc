#!/bin/bash
rm -rf bin src/version.py
find . -type f -name "*.pyc" -exec rm -f {} \;
find tests -type f -name "*.out" -exec rm -f {} \;
find tests -type f -name "*.out.*" -exec rm -f {} \;
find tests -type f -name "*.o" -exec rm -f {} \;
find tests -type f -name "*.asm" -exec rm -f {} \;
find tests -type f -name "*.exe" -exec rm -f {} \;
