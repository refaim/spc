@echo off

rem py2exe build script

echo pre-build cleaning...
call clean.bat

echo creating the executable...
cd src
C:\Python26\python.exe setup.py py2exe
cd ..

echo post-build actions...
move src\dist bin >nul
del /Q bin\w9xpopen.exe
xcopy /E /I tests bin\tests >nul

cd bin
echo @echo off > run.bat
echo OLDPATH=%%PATH%% >> run.bat
echo PATH=%%CD%%\..\utils\graphviz\bin;%%PATH%% >> run.bat
echo %%* >> run.bat
echo set PATH=%%OLDPATH%% >> run.bat
cd ..

rd /S /Q src\build 2>nul
