@echo off

if not exist src\version.py call configure.bat
set tester=python %~dp0src\tester.py
%tester% -a %*
