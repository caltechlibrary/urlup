'''
__main__: main command-line interface to urlup

Authors
-------

Michael Hucka <mhucka@caltech.edu>

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software.  Please see the file "LICENSE" for more information.
'''

import csv
import os
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
    explain  = ('print explanations of HTTP codes',                'flag',   'e'),
    input    = ('input file to read',                              'option', 'i'),
    output   = ('output file to write',                            'option', 'o'),
    quiet    = ('do not print messages while working',             'flag',   'q'),
    no_color = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    version  = ('print version info and exit',                     'flag',   'V'),
    urls     = 'URLs to check',
)

def main(input=None, output=None, explain = False, quiet=False, no_color=False,
         version=False, *urls):
    '''Find the ultimate destination for URLs after following redirections.

If the command-line option -i is not provided, this program assumes that the
URLs to be checked are supplied on the command line.  If -i is used, the URLs
should be written one per line in the file.

If the option -o is used, data is written in comma-separated format to the
given file, with each row containing the following information:

  original url, final url, http code

The http code is the code returned by the server when the original url is
accessed.  The final url is the ultimate URL that results after following
redirections (if any).

Even if writing the output to a file, this program will print information to
the terminal as it processes URLs, unless the option -q is given.
'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color

    # Process arguments
    if version:
        print('{} version {}'.format(urlup.__title__, urlup.__version__))
        print('Author: {}'.format(urlup.__author__))
        print('URL: {}'.format(urlup.__url__))
        print('License: {}'.format(urlup.__license__))
        sys.exit()

    if not input and not urls:
        raise SystemExit(color('Need a file or URLs as argument', 'error', colorize))

    if not output and not quiet:
        msg("No output file specified; results won't be saved.", 'warn', colorize)
    elif not quiet:
        msg('Output will be written to {}'.format(output, 'info', colorize))

    results = []
    if input:
        if os.path.exists(input):
            if not quiet:
                msg('Reading URLs from {}'.format(input), 'info', colorize)
            with open(input) as f:
                lines = map(str.rstrip, f.readlines())
                results = updated_urls(lines, colorize, quiet, explain)
        elif os.path.exists(os.path.join(os.getcwd(), file)):
            full_path = os.path.join(os.getcwd(), file)
            if not quiet:
                msg('Reading URLs from {}'.format(full_path), 'info', colorize)
            with open(full_path) as f:
                lines = map(str.rstrip, f.readlines())
                results = updated_urls(lines, colorize, quiet, explain)
        else:
            raise SystemExit(color('Cannot find file "{}"'.format(input), 'error', colorize))
    else:
        # Not given a file.  Do the arguments look like URLs?  If so, use them.
        parts = urisplit(urls[0])
        if not parts.scheme:
            raise SystemExit(color('{} does not appear to be a proper URI'.format(urls[0]),
                                   'error', colorize))
        results = updated_urls(urls, colorize, quiet, explain)

    if not results:
        msg('No results returned.')
        sys.exit()

    if output:
        if not quiet:
            msg('Writing CSV file {}'.format(output), 'info', colorize)
        with open(output, 'w', newline='') as out:
            csvwriter = csv.writer(out, delimiter=',')
            csvwriter.writerows(results)

    if not quiet:
        msg('Done.', 'info', colorize)


# The following allows users to invoke this using "python3 -m urlup".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
