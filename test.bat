@echo off

set reqfile=src\version.py

if not exist %reqfile% call configure.bat
if errorlevel 1 call clean.bat && exit
python %~dp0src\tester.py %*
