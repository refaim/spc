@echo off
rd /s /q bin 2>nul >nul
del /s /q *.pyc 2>nul >nul
del /q src\version.py 2>nul >nul
del /q *.gif 2>nul >nul