# -*- coding: utf-8 -*-

from errors import LexError
from token import tt, dlm, keywords
from syn import SynBinaryOp

lexems_str = { tt.identifier: "Identifier", tt.integer: "Integer",
               tt.float: "Float", tt.char_const: "Character constant",
               tt.string_const: "String constant", tt.wrong: "Wrong token",
 
               dlm.plus: "Plus", dlm.lesser: "Less", dlm.assign: "Assignmnent",
               dlm.lparen: "Left parenthesis", dlm.minus: "Minus",
               dlm.greater: "Greater", dlm.semicolon: "Semicolon",
               dlm.rparen: "Right parenthesis", dlm.mul: "Asterix",
               dlm.lesser_or_equal: "Less or equal", dlm.colon: "Colon",
               dlm.lsbracket: "Left square bracket", dlm.div: "Div",
               dlm.greater_or_equal: "Greater or equal", dlm.dot: "Dot",
               dlm.rsbracket: "Right square bracket", dlm.equal: "Equal",
               dlm.comma: "Comma", dlm.not_equal: "Not equal",
               dlm.double_dot: "Double dot"
             }

def get_string_repr(lexem):
    s = str(lexem).lower()
    if lexem in lexems_str:
        return lexems_str[lexem]
    elif s in keywords:
        return "{0} (keyword)".format(s).capitalize()
    else:
        return ""

def get_token_array(tokenizer):
    t = tokenizer.get_token()
    tokens = []
    try:
        while t != None:
            tokens.append(t)
            tokenizer.next_token()
            t = tokenizer.get_token()
    except LexError as lexerr:
        return tokens, lexerr        
    return tokens, None

space = " "
indent_len = 2
indent = indent_len * space
b_horz, b_vert, b_cross = "-", "|", "+"

def print_token_array(tokens):

    if len(tokens) == 0:
        exit()
    
    colcount = 5
    headers = ["Line, pos", "Token text", "Token value", "Token type", "Error"]

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
        return [linepos_template.format(tok.line, tok.pos), tok.text, str(tok.value), get_string_repr(tok.type), tok.errmsg]
    
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
            lshift = (a - b) // 2 if a > b else 0
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

def print_syntax_tree(root):

    def binary(node):
        return isinstance(node, SynBinaryOp)

    def calc_dimensions(node):
        std_node_height = 3
        std_borders_width = 4

        strlen = len(str(node)) + std_borders_width
        if binary(node):
            (wl, hl), (wr, hr) = calc_dimensions(node.opleft), calc_dimensions(node.opright)
            w = wl + wr + strlen + 2
            h = max(hl, hr) + std_node_height
        else:
            w = strlen
            h = std_node_height
        widths[node], heights[node] = w, h
        return w, h

    heights, widths = {}, {}

    calc_dimensions(root)
    out = [' ' * widths[root]] * heights[root]

    def frame(text, b1, b2 = ""):
        if b2 == "":
            b2 = b1
        return [b1, text, b2]

    def selfwidth(node):
        return widths[node] - widths[node.opleft] - widths[node.opright]

    def print_node(node, x, y, lbound, rbound):
        if binary(node):
            print_binary(node, x, y, lbound, rbound)
        else:
            print_simple(node, x, y)

    def print_simple(node, x, y):
        text = b_vert + space + str(node) + space + b_vert
        border = b_cross + b_horz * (len(text) - len(b_cross) * 2) + b_cross

        box = frame(text, border)
        for s in box:
            out[x] = out[x][:y] + s + out[x][y + widths[node]:]
            x += 1

    def print_binary(node, x, y, lbound, rbound):
        text = b_cross + indent + str(node) + indent + b_cross

        # left branch
        if binary(node.opleft):
            shift = selfwidth(node.opleft) // 2
            lbpos = y - widths[node.opleft.opright] - shift
            new_left_y = lbpos - shift - 1
        else:
            shift = widths[node.opleft] // 2
            lbpos = y - shift
            new_left_y = lbpos - shift#max(0, lbpos - shift, lbpos)
        lblen = y - lbpos
        lb = b_cross + b_horz * lblen

        # right branch
        rside = y + selfwidth(node)
        if binary(node.opright):
            shift = selfwidth(node.opright) // 2
            rbpos = rside + widths[node.opright.opleft] + shift 
            new_right_y = rbpos - shift + 1
        else:
            shift = widths[node.opright] // 2
            rbpos = rside + shift
            new_right_y = rbpos - max(shift // 2 + shift % 2, shift - 2) #min(rbpos, rbpos - shift - 1)
        rblen = rbpos - rside + 1
        rb = b_horz * rblen + b_cross

        border_template = space * lblen + b_cross + b_horz * (len(text) - len(b_cross) * 2) + b_cross + space * rblen
        top_border = space + border_template + space
        btm_border = b_vert + border_template + b_vert
        text = lb + text + rb

        box = frame(text, top_border, btm_border)
        for s in box:
            out[x] = out[x][:lbpos] + s + out[x][rbpos:]
            x += 1

        print_node(node.opleft, x, new_left_y, lbound, y)
        print_node(node.opright, x, new_right_y, rside, rbound)

    y = widths[root.opleft] if binary(root) else 0
    print_node(root, 0, y, 0, widths[root])

    for s in out:
        print(s.rstrip(" "))
    print(b_horz * widths[root])
