@echo off

echo Configuring CMake...
call configure.bat

echo Pre-build testing...
call test.bat
if errorlevel 1 exit

pushd bin
echo Building...
make
copy dist\spc.exe . >nul
popd
