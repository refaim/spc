# -*- coding: utf-8 -*-

def first(seq):
    return seq[0] if seq else None

def second(seq):
    return seq[1] if seq and len(seq) >= 2 else None

def last(seq):
    return seq[len(seq) - 1] if seq and not empty(seq) else None

def empty(seq):
    return len(seq) == 0

def subscript(seq, elm):
    return seq[elm] if elm in seq else None
