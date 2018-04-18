'''
cli_main: main command-line interface to urlup
'''

import csv
import os
import plac
import sys
try:
    from termcolor import colored
except:
    pass

# Allow this program to be executed directly from the 'bin' directory.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import urlup
from urlup import updated_urls
from urlup.messages import color, msg


# Main program.
# ......................................................................

@plac.annotations(
    input    = ('input file to read',                                'option', 'i'),
    output   = ('output file to write',                              'option', 'o'),
    quiet    = ('do not print messages while working',               'flag',   'q'),
    version  = ('print version info and exit',                       'flag',   'v'),
    no_color = ('do not color-code terminal output (default: do)',   'flag',   'C'),
    urls     = 'URLs to check',
)

def cli_main(input=None, output=None, quiet=False, version=False, no_color=False, *urls):
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

    if not output:
        msg("No output file given -- results won't be saved.", 'warn', colorize)
    else:
        msg('Output will be written to {}'.format(output, 'info', colorize))

    results = []
    if input:
        if os.path.exists(input):
            if not quiet:
                msg('Reading URLs from {}'.format(input), 'info', colorize)
            with open(input) as f:
                lines = map(str.rstrip, f.readlines())
                results = updated_urls(lines, colorize, quiet)
        elif os.path.exists(os.path.join(os.getcwd(), file)):
            full_path = os.path.join(os.getcwd(), file)
            if not quiet:
                msg('Reading URLs from {}'.format(full_path), 'info', colorize)
            with open(full_path) as f:
                lines = map(str.rstrip, f.readlines())
                results = updated_urls(lines, colorize, quiet)
        else:
            raise ValueError('Cannot find file "{}"'.format(input))
    else:
        results = updated_urls(urls, colorize, quiet)

    if not results:
        msg('No results returned.')
        sys.exit()

    if output:
        if not quiet:
            msg('Writing CSV file {}'.format(output), 'info', colorize)
        with open(output, 'w', newline='') as out:
            csvwriter = csv.writer(out, delimiter=',')
            csvwriter.writerows(results)

    msg('Done.', 'info', colorize)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End: