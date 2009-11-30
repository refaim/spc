# -*- coding: utf-8 -*-

def first(seq):
    return seq[0] if seq else None

def second(seq):
    return seq[1] if seq and len(seq) >= 2 else None

def some(seq):
    for x in seq:
        if x: return x
    return None

def empty(seq):
    return len(seq) == 0

def sort(seq):
    if seq:
        seq.sort()
        return seq
    return None
