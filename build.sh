#!/bin/bash
echo 'Configuring CMake...'
./configure.sh
if [ "$?" -ne "0" ]; then
    exit 1
fi

echo 'Pre-build testing...'
./test.sh -a
if [ "$?" -ne "0" ]; then
    exit 1
fi

cd bin
echo 'Building...'
make
if [ "$?" -eq "0" ]; then
    cp dist\spc ..
    cd ..
fi
