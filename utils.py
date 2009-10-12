# -*- coding: utf-8 -*-

from constants import lexems_str
from exceptions import MyLexicalError

def get_token_array(tokenizer):
    t = tokenizer.get_token()
    tokens = []
    try:
        while t != None:
            tokens.append(t)
            tokenizer.next_token()
            t = tokenizer.get_token()
    except MyLexicalError as lexerr:
        return tokens, lexerr        
    return tokens, None

def print_token_array(tokens):

    if len(tokens) == 0:
        exit()
    
    space = " "
    indent_len = 2
    indent = indent_len * space
    b_horz, b_vert, b_cross = "-", "|", "+"
    
    colcount = 5
    headers = ["Line, pos", "Token text", "Token value", "Token type", "Error"]
    right_align = [0]

    # разделители + пустые строки + заголовок + основной массив
    rowcount = 3 + 4 + 1 + len(tokens)

    # номера строк
    empty_lines = [1, 3, 5, 5 + len(tokens) + 1]
    borders = [0, 4, rowcount - 1]
    header = 2

    # перед токенами два разделителя, три пустых строки и заголовок
    tokens_shift = (len(empty_lines) - 1) + (len(borders) - 1) + 1

    linepos_template = "{0}, {1}"
    def values(tok):
        return [linepos_template.format(tok.line, tok.pos), tok.text, str(tok.value), lexems_str[tok.type], tok.errmsg]
    
    def print_line(out, row, col):
        left_border = b_vert if col == 0 else ""
        left, right = left_border + indent, indent + b_vert
        emptyline = left + max_value_lens[col] * space + right
        
        if row in borders:
            length = max_value_lens[col] + len(left + right)
            right_border = b_cross if col == colcount - 1 else ""            
            out[row] += b_cross + b_horz * (length - len(left_border + b_vert)) + right_border 
        elif row in empty_lines:
            out[row] += emptyline
        elif row == header:
            a, b = max_value_lens[col], len(headers[col])
            lshift = int((a - b) / 2) if a > b else 0
            rshift = max_value_lens[col] - len(headers[col]) - lshift
            out[row] += left + space * lshift + headers[col] + space * rshift + right
        else:
            tok = tokens[row - tokens_shift]
            value = values(tok)[col]
            rshift = max_value_lens[col] - len(value)
            out[row] += left + value + space * rshift + right

    max_value_lens = [0] * colcount

    errors_present = False
    for tok in tokens:
        if tok.error: errors_present = True
        for i in range(colcount):
            max_value_lens[i] = max(len(headers[i]), len(values(tok)[i]), max_value_lens[i])

    if not errors_present:
        colcount -= 1

    out = [""] * rowcount   
    for row in range(rowcount):
        for col in range(colcount):
            print_line(out, row, col)

    for s in out:
        print(s)
