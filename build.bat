@echo off

mkdir bin 2>nul
pushd bin
echo Configuring CMake...
call cmake -G "Unix Makefiles" ..
popd

echo Pre-build testing...
call test.bat
if errorlevel 1 exit

pushd bin
echo Building...
make
copy dist\spc.exe . >nul
popd
