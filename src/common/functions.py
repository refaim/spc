# -*- coding: utf-8 -*-

def first(seq):
    return seq[0] if seq else None

def second(seq):
    return seq[1] if seq and len(seq) >= 2 else None

def last(seq):
    return seq[-1] if seq and nonempty(seq) else None

def empty(seq):
    return len(seq) == 0

def nonempty(seq):
    return len(seq) != 0

import inspect
import functools

def copy_args(func):
    ''' Initializes object attributes by the initializer signature '''
    argspec = inspect.getargspec(func)
    argnames = argspec.args[1:]
    
    if argspec.defaults:
        defaults = dict(zip(argnames[-len(argspec.defaults):], argspec.defaults))
    else:
        defaults = {}

    @functools.wraps(func)
    def __init__(self, *args, **kwargs):
        args_it = iter(args)
        for key in argnames:
            if key in kwargs:
                value = kwargs[key]
            else:
                try:
                    value = args_it.next()
                except StopIteration:
                    value = defaults[key]
            setattr(self, key, value)
        func(self, *args, **kwargs)
    return __init__