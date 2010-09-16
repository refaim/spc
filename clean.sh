#!/bin/bash
rm -rf bin src/version.py
find . -type f -name "*.pyc" -exec rm -f {} \;
find . -type f -name "*.out" -exec rm -f {} \;
find . -type f -name "*.out.*" -exec rm -f {} \;
