@echo off
mkdir bin >nul 2>&1
pushd bin
call cmake -G "Unix Makefiles" ..
popd
