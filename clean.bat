@echo off
pushd %~dp0
rd /s /q bin >nul 2>&1
call :delete /s *.pyc
call :delete src\version.py
pushd tests
call :delete /s *.out.*
pushd gen
call :delete /s *.asm *.o *.exe
popd
popd
popd
goto :eof

:delete
    del /q %* >nul 2>&1
    exit /b 0
