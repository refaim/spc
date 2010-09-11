@echo off
rd /s /q bin >nul 2>&1
del /s /q *.pyc *.o.* >nul 2>&1
del /q src\version.py >nul 2>&1
del /q *.gif *.dot >nul 2>&1
