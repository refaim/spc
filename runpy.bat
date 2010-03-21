@echo off
set OLDPATH=%PATH%
set PATH=%CD%\utils\graphviz\bin;%PATH%
if "%~x1" == ".py" (set SCRIPT=%1) else (set SCRIPT=%1.py)
src\%SCRIPT% %2 %3 %4 %5
set PATH=%OLDPATH%
