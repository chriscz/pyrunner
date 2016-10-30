"""
    A script for writing and automating tasks in python. It's
    a lightweight alternative to Fabricate (https://github.com/SimonAlfie/fabricate/),
    and Fabric. 
    
    And can be used in the place of shell scripts. Extensions are welcome.
    
    See example.py for a full usage example.
"""
from __future__ import print_function

import sys
import os
import inspect

from textwrap import fill
from subprocess import Popen, PIPE, CalledProcessError

# --- constants
DEFAULT_ACTION = 'default'

def run(*args, **kwargs):
    """
    Runs a command on the underlying system. 

    Optional Keyword Arguments
    --------------------------
    input: string
        passed to the Popen.communicate call as input

    timeout: millisecond float
        specifies how long to wait before terminating the given command  
    """
    assert len(args) > 0

    arguments = []

    input = kwargs.pop('input', None)

    if len(args) == 1:
        if isinstance(args[0], basestring):
            arguments = args[0].split()
    else:
        for i in args:
            if isinstance(i, (list, tuple)):
                for j in i:
                    arguments.append(j)
            else:
                arguments.append(i)

    proc = Popen(arguments, stdin=PIPE, stdout=PIPE, stderr=PIPE, **kwargs)
    stdout, stderr = proc.communicate(input)
    return proc.returncode, stdout, stderr

# --- internally used functions
def _build_func_text(function, name=None):
    spec = inspect.getargspec(function)
    doc = inspect.getdoc(function)
    name = name or function.__name__
    args = list(spec.args)

    NO_DEFAULT = object()
    defaults = spec.defaults or []
    defaults = [NO_DEFAULT]*(len(args) - len(defaults)) + list(defaults)

    if spec.varargs:
        args += [spec.varargs]
        defaults += [NO_DEFAULT]

    if spec.keywords:
        args += [spec.keywords]
        defaults += [NO_DEFAULT]

    line = name + '('
    for i, (arg, dv) in enumerate(zip(args, defaults)):
        if arg  == spec.varargs:
            line += '*' + arg
        elif arg == spec.keywords:
            line += '**' + arg
        else:
            line += arg
        
        if dv != NO_DEFAULT:
            line += '='
            line += repr(dv)
        line += ', '

    if defaults:
        line = line[:-2]

    line += ')'

    return line, doc

def format_docstring(docstring, indent=' '*4):
    lines = []
    for line in docstring.splitlines():
        lines.append(fill(line, width=80, initial_indent=indent, subsequent_indent=indent))
    return '\n'.join(lines)

def main(globals_dict=None, args=None, default=DEFAULT_ACTION):
    # preprocess all the arguments
    if args is None:
        args = sys.argv[1:]

    if globals_dict is None:
        frame = sys._getframe(1)
        globals_dict = frame.f_globals

    # collect all the functions
    values = globals().values()
    filtered = {}
    for i in globals_dict:
        v = globals_dict[i]
        if inspect.isfunction(v) and\
           inspect.getfile(v) != __file__ and\
           v not in values:
            filtered[i] = v

    # --- begin the execution
    if not args and default in filtered:
        exec(i, globals_dict, dict())
    elif not args: # then list the available commands
        print("Commands")
        for name in filtered:
            value = filtered[name]
            line, doc = _build_func_text(value, name)
            print('- {}'.format(line))
            if doc is not None:
                print(format_docstring(doc))
        sys.exit(1)
    else:
        # process any function calls
        for i in args:
            if '(' not in i:
                i += '()'
            name = i[:i.index('(')]
            if name not in filtered:
                print("{} is not a recognized function".format(name))
                sys.exit(1)
            exec(i, globals_dict, dict())
