# -*- coding: utf-8 -*-

class MyCompilerError(BaseException):
    def __init__(self, message):
        self.message = message

class MyLexicalError(MyCompilerError): pass
class MySyntaxError(MyCompilerError): pass

common_template = "{error} on line {l}, col {p}. {text}"

# lexical errors
lex_count = 2
lex_eof_bc, lex_eof_str = range(2)

# syntax errors
syn_count, shift = 2, lex_count
syn_unexp_token, syn_par_mismatch = range(shift, shift + syn_count)

errors = { lex_eof_bc: "Unexpected end of file in block comment",  
           lex_eof_str: "Unexpected end of file in string literal", 
         
           syn_unexp_token: "Expected constant expression or identifier",
           syn_par_mismatch: "Parenthesis mismatch" 
         }
         
errbycode = { lex_eof_bc: MyLexicalError, lex_eof_str: MyLexicalError,
              syn_unexp_token: MySyntaxError, syn_par_mismatch: MySyntaxError }
              
commonerr = { MyLexicalError: "Lexical error", MySyntaxError: "Syntax error" }          

def raise_error(errcode, filepos):
    line, pos = filepos
    errtype, errmsg = errbycode[errcode], errors[errcode]
    raise errtype(common_template.format(error = commonerr[errtype], 
                                         l = line, p = pos, 
                                         text = errmsg))