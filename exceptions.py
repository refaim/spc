# -*- coding: utf-8 -*-

class MyCompilerError(BaseException):
    def __init__(self, message):
        self.message = message

class MyLexicalError(MyCompilerError): pass
class MySyntaxError(MyCompilerError): pass

# лексические ошибки
lex_count = 2
lex_eof_bc, lex_eof_str = range(2)

# синтаксические ошибки
syn_count = 2
shift = lex_count
syn_unexp_token, syn_par_mismatch = range(shift, shift + syn_count)


error_messages = { lex_eof_bc: "Unexpected end of file in block comment",  
                   lex_eof_str: "Unexpected end of file in string literal", 
         
                   syn_unexp_token: "Expected constant expression or identifier",
                   syn_par_mismatch: "Parenthesis mismatch" 
                 }
         
common_messages = { MyLexicalError: "Lexical error", MySyntaxError: "Syntax error" }          
common_template = "{error} on line {l}, col {p}. {text}"

def raise_error(errcode, filepos):
    line, pos = filepos
    errclass = MyLexicalError if errcode < lex_count else MySyntaxError
    raise errclass(common_template.format(error = common_messages[errclass], 
                                         l = line, p = pos, 
                                         text = error_messages[errcode]))