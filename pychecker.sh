#!/bin/sh
for entry in $(ls | grep '.py$')
do
	if [ $entry != 'enum.py' ]
	then
		pychecker $entry | less
	fi
done         
