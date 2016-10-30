"""
    Default Function
    ----------------
    when a function default is defined within the namespace, that 
    function will be executed if no arguments are provided

    Usage Examples
    --------------
    Print out the possible commands
        $ python example.py 
    
    Some execution examples
        $ python example.py 'foo'
          foo says hello

        $ python example.py 'foo(1)'
          foo says 1

        $ python example.py 'bar(1, darg=88, -1, -2, fan=False)'
          arg 1
          darg 88
          args (-1, -2)
          kwargs {'fan': False}

        $ python example.py 'foo("hello")' 'foo("bye")'
          foo says hello
          foo says bye

"""
from __future__ import print_function
from pyrunner import *

def foo(msg='hello'):
    """Let foo speak
    
        Returns
        -------
        None
    """
    print("foo says", msg)

def bar(arg, darg=1, *star, **stars):
    print('arg', arg)
    print('darg', darg)
    print('args', star)
    print('kwargs', stars)

# should always call main at the end
main()


