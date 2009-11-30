# -*- coding: utf-8 -*-

def abstract(func):
    def closure(*dt, **mp):
        raise NotImplementedError(
            'Method {0} is pure virtual'.format(func.__name__))
        return closure

def first(seq):
    return seq[0] if seq else None

def second(seq):
    return seq[1] if seq and len(seq) >= 1 else None

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
