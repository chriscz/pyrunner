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

from contextlib import contextmanager
from collections import namedtuple
from StringIO import StringIO

import argparse

RunResult = namedtuple('RunResult', ['returncode', 'stdout', 'stderr'])

# --- constants
DEFAULT_ACTION = 'default'

@contextmanager
def silence():
    """
    suppresses any stdout / stderr output from the code in this context

    Example
    -------
    >>> with silence():
    >>>    print "hello"
    >>> print "there"
    there
    """
    o_out = sys.stdout
    o_err = sys.stderr
    try:
        with open(os.devnull, 'w') as nil:
            sys.stdout = nil
            sys.stderr = nil
            yield
    finally:
        sys.stderr = o_err
        sys.stdout = o_out

@contextmanager
def cd(directory):
    """
    Context manager that changes the working directory in the given context.

    Example
    -------

    with cd('/home/'):
        # do some stuff
    """
    old = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(old)

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

    return RunResult(proc.returncode, stdout, stderr)

# --- internally used functions

def parse_args(args):
    parser = argparse.ArgumentParser(prog='pyrunner.py', 
                                     description='A script for writing and automating tasks in python')

    parser.add_argument('function', nargs='*')
    parser.add_argument('-H', '--hidden',
                        help='show functions which have a name starting with _ (underscore)',
                        action='store_true')
    parser.add_argument('-l', '--list', 
                        help='lists all the available functions',
                        action='store_true')

    return parser.parse_args(args)



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

def get_functions(globals_dict, only_file=None, show_hidden=False):
    # collect all the functions
    this_file = os.path.abspath(__file__)

    def keep_item((name, value)):
        dfile = lambda: inspect.getabsfile(value)
        is_hidden_name = lambda: name.startswith('_')

        keep = True
        keep = keep and (show_hidden or not is_hidden_name())
        keep = keep and inspect.isfunction(value)
        keep = keep and dfile() != this_file
        keep = keep and (not only_file or dfile() == only_file) 
        return keep
    
    return dict(filter(lambda i: i if keep_item(i) else None, globals_dict.items()))

def action_list_functions(functions):
    print("Commands")
    for name in functions:
        value = functions[name]
        line, doc = _build_func_text(value, name)
        print('- {}'.format(line))
        if doc is not None:
            print(format_docstring(doc))


def main(globals_dict=None, args=None, commandfile=None,  default=DEFAULT_ACTION):
    # preprocess all the arguments
    if args is None:
        args = sys.argv[1:]
    
    parsed = parse_args(args)

    if globals_dict is None:
        frame = sys._getframe(1)
        globals_dict = frame.f_globals

    if commandfile is None:
        frame = sys._getframe(1)
        finfo = inspect.getframeinfo(frame)
        commandfile = os.path.abspath(finfo.filename)
        
    functions = get_functions(globals_dict, only_file=commandfile, show_hidden=parsed.hidden)

    if parsed.list:
        action_list_functions(functions)
        sys.exit(1)

    # --- begin the execution
    if default in functions and not args:
        exec(default + '()', globals_dict, dict())
    elif not args: # then list the available commands
        action_list_functions(functions)
        sys.exit(1)
    else:
        # process any function calls
        for i in parsed.function: # XXX name here is singular due to argparse
            if '(' not in i:
                i += '()'
            name = i[:i.index('(')]
            if name not in functions:
                print("{} is not a recognized function".format(name))
                sys.exit(1)
            exec(i, globals_dict, dict())
