#!/bin/bash
mkdir bin 2>/dev/null
cd bin
cmake -G "Unix Makefiles" ..
cd ..
