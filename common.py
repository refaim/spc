# -*- coding: utf-8 -*-

def first(seq):
    return seq[0] if seq else None

def some(seq):
    for x in seq:
        if x: return x
    return None

def empty(seq):
    return len(seq) == 0
