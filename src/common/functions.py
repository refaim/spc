# -*- coding: utf-8 -*-

import inspect
import functools

def quote(string):
    return '"' + string + '"'

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
