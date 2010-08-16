@echo off

set tester=python %~dp0src\tester.py
%tester% -a %*
