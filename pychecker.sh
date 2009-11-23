#!/bin/sh
for entry in $(ls | grep '.py$')
do 
	pychecker $entry
	read none
done
