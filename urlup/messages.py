'''
messages: message-printing utilities

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import sys

try:
    from termcolor import colored
    if sys.platform.startswith('win'):
        import colorama
        colorama.init()
except ImportError:
    pass


def print_header(text, flags, quiet = False, colorize = True):
    if not quiet:
        msg('')
        msg('{:-^78}'.format(' ' + text + ' '), flags, colorize)
        msg('')


def msg(text, flags = None, colorize = True):
    '''Like the standard print(), but flushes the output immediately and
    colorizes the output by default. Flushing immediately is useful when
    piping the output of a script, because Python by default will buffer the
    output in that situation and this makes it very difficult to see what is
    happening in real time.
    '''
    if colorize:
        print(color(text, flags), flush = True)
    else:
        print(text, flush = True)


def color(text, flags = None, colorize = True):
    (prefix, color_name, attributes) = color_codes(flags)
    if colorize:
        if attributes and color_name:
            return colored(text, color_name, attrs = attributes)
        elif color_name:
            return colored(text, color_name)
        elif attributes:
            return colored(text, attrs = attributes)
        else:
            return text
    elif prefix:
        return prefix + ': ' + text
    else:
        return text


def color_codes(flags):
    color_name  = ''
    prefix = ''
    if type(flags) is not list:
        flags = [flags]
    if sys.platform.startswith('win'):
        attrib = [] if 'dark' in flags else ['bold']
    else:
        attrib = []
    if 'error' in flags:
        prefix = 'ERROR'
        color_name = 'red'
    if 'warning' in flags or 'warn' in flags:
        prefix = 'WARNING'
        color_name = 'yellow'
    if 'info' in flags:
        color_name = 'green'
    if 'white' in flags:
        color_name = 'white'
    if 'blue' in flags:
        color_name = 'blue'
    if 'grey' in flags:
        color_name = 'grey'
    if 'cyan' in flags:
        color_name = 'cyan'
    if 'magenta' in flags:
        color_name = 'magenta'
    if 'underline' in flags:
        attrib.append('underline')
    if 'bold' in flags:
        attrib.append('bold')
    if 'reverse' in flags:
        attrib.append('reverse')
    if 'dark' in flags:
        attrib.append('dark')
    return (prefix, color_name, attrib)


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
