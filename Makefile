clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '*.swp' -delete
	find -name '*.o' -delete
	find -name '*.o.gif' -delete
	find -name '.gedit*' -delete

test:
	echo "Lexical analyzer:" && ./tester.py -l && echo 
	echo "Syntax analyzer (arithmetic expressions):" && ./tester.py -e && echo
	echo "Syntax analyzer (simple declarations):" && ./tester.py -s
