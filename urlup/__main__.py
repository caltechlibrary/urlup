'''
__main__: main command-line interface to urlup.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import csv
import os
import os.path as path
import plac
import sys
try:
    from termcolor import colored
except:
    pass
from   uritools import urisplit

import urlup
from urlup import updated_urls
from urlup.messages import color, msg


# Main program.
# ......................................................................

@plac.annotations(
    explain  = ('print explanations of HTTP codes encountered',    'flag',   'e'),
    input    = ('read URLs from file F',                           'option', 'i'),
    output   = ('write results to file R',                         'option', 'o'),
    quiet    = ('do not print messages while working',             'flag',   'q'),
    no_color = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    version  = ('print version info and exit',                     'flag',   'V'),
    url      = 'URL to dereference (can supply more than one)',
)

def main(explain = False, input="F", output="R", quiet=False, no_color=False,
         version=False, *url):
    '''Find the ultimate destination for URLs after following redirections.

If the command-line option -i is not provided, this program assumes that the
URLs to be checked are supplied on the command line.  If -i is used, the URLs
should be written one per line in the file.

If the option -o is used, data is written in comma-separated (CSV) format to
the given file, with each row containing the following columns:

  original url, final url, http code, error

The "http code" is the code returned by the server when the "original url" is
accessed.  The "final url" is the ultimate URL that results after following
redirections (if any).  If an input generates an error, the "final url" will
be empty, and an error message will be given in the "error" colum.

Even if writing the output to a file, this program will print information to
the terminal as it processes URLs, unless the option -q is given to make it
more quiet.
'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color

    # Some user interactions change depending on the current platform.
    on_windows = sys.platform.startswith('win')

    # Process arguments
    if version:
        print('{} version {}'.format(urlup.__title__, urlup.__version__))
        print('Author: {}'.format(urlup.__author__))
        print('URL: {}'.format(urlup.__url__))
        print('License: {}'.format(urlup.__license__))
        sys.exit()

    if on_windows:
        get_help = '(Hint: use /h to get help.)'
    else:
        get_help = '(Hint: use -h to get help.)'
    if input == 'F' and not path.exists('F'):
        input = None
    if output == 'R':
        output = None
    if not input and not url:
        raise SystemExit(color('Need a file or URLs as argument. ' + get_help,
                               'error', colorize))
    if not input and url and url[0].startswith(('-', '/') if on_windows else '-'):
        # It starts with a dash but not recognized by plac and can't be a URL.
        raise SystemExit(color(('Unrecognized argument "{}". ' + get_help).format(url[0])))
    if not output and not quiet:
        msg("No output file specified; results won't be saved.", 'warn', colorize)
    elif not quiet:
        rename_if_existing(output, colorize)

    results = []
    try:
        if input:
            urls = []
            file_path = None
            if path.exists(input):
                file_path = input
            elif path.exists(path.join(os.getcwd(), input)):
                file_path = path.join(os.getcwd(), input)
            else:
                raise SystemExit(color('Cannot find file "{}"'.format(input),
                                       'error', colorize))
            if not quiet:
                msg('Reading URLs from {}'.format(file_path))
            with open(file_path) as f:
                urls = map(str.rstrip, f.readlines())
        else:
            # Not given a file.  Do the arguments look like URLs?  If so, use them.
            urls = url[0]
            parts = urisplit(urls)
            if not parts.scheme and not parts.path:
                raise SystemExit(color('{} does not appear to be a URL'.format(urls),
                                       'error', colorize))
        results = updated_urls(urls, quiet, explain, colorize)
    except KeyboardInterrupt:
        msg('Quitting.')

    if not results:
        msg('No results returned.')
        sys.exit()
    elif output:
        if not quiet:
            msg('Writing CSV file {}'.format(output))
        with open(output, 'w', newline='') as out:
            csvwriter = csv.writer(out, delimiter=',')
            for data in results:
                csvwriter.writerow([data.original, data.final or '',
                                    data.status, data.error or ''])
    elif quiet:
        # Rationale for the sense of the test against the "quiet" argument:
        # If we were being quiet, no other info will be printed.  Conversely,
        # if we weren't being quiet, then the following would be redundant.
        msg('Results:')
        for item in results:
            if item.error:
                msg('Encountered error {} dereferencing {}'
                    .format(item.error, item.original), 'error', colorize)
            elif not item.final:
                msg('Could not dereference {}'.format(item.original), 'warn', colorize)
            else:
                msg('{} => {}'.format(color(item.original, 'info', colorize),
                                      color(item.final, 'info', colorize)))
        msg('Done.')


# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if sys.platform.startswith('win'):
    main.prefix_chars = '/'


# Miscellaneous utilities.
# ......................................................................

def rename_if_existing(file, colorize):
    def rename(f):
        backup = f + '.bak'
        msg('Renaming existing file {} to {}'.format(f, backup), 'warn', colorize)
        os.rename(f, backup)

    if path.exists(file):
        rename(file)
        return
    full_path = path.join(os.getcwd(), file)
    if path.exists(full_path):
        rename(full_path)
        return


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m urlup".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
