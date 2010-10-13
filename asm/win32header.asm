format PE console
entry main

include '{0}'

section '.idata' import data readable

library kernel, 'kernel32.dll',\
        msvcrt, 'msvcrt.dll'

import kernel, ExitProcess, 'ExitProcess'
import msvcrt, printf, 'printf'

