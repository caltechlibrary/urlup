'''
__main__: main command-line interface to urlup.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import csv
import os
import os.path as path
import plac
import requests
import sys
try:
    from termcolor import colored
except ImportError:
    pass
from   uritools import urisplit

import urlup
from urlup import updated_urls
from urlup.messages import color, msg


# Main program.
# ......................................................................

@plac.annotations(
    cookies    = ('list of cookie value pairs separated by commas',  'option', 'c'),
    explain    = ('print explanations of HTTP codes encountered',    'flag',   'e'),
    input      = ('read URLs from file F',                           'option', 'i'),
    output     = ('write results to file R',                         'option', 'o'),
    pswd       = ('proxy user password',                             'option', 'p'),
    user       = ('proxy user name',                                 'option', 'u'),
    quiet      = ('do not print messages while working',             'flag',   'q'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    reset      = ('reset proxy user name and password',              'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
    no_keyring = ('do not use a keyring',                            'flag',   'X'),
    url        = 'URL to dereference (can supply more than one)',
)

def main(cookies = {}, explain = False,
         input='F', output='R', user = 'U', pswd = 'P',
         quiet=False, no_color=False, reset=False, no_keyring=False,
         version=False, *url):
    '''Find the ultimate destination for URLs after following redirections.

If the command-line option -i (or /i on Windows) is not provided, this
program assumes that the URLs to be checked are supplied on the command line.
If the option -i is used, the URLs should be written one per line in a file
whose name is provided as the value following the -i option.

If the option -o (or /o on Windows) is used, data is written in a
comma-separated (CSV) format to the file named after the -o option.  Each
row of the CSV file will contain the following columns:

   original url, final url, http code, error

The "http code" column is the code returned by the server when the "original
url" is accessed.  The "final url" is the ultimate URL that results after
following redirections (if any).  If an input generates an error, the "final
url" will be empty, and an error message will be given in the "error" colum.

If the URLs to be dereference involve a proxy server (such as EZproxy, a
common type of proxy used by academic institutions), it will be necessary to
supply login credentials for the proxy component.  By default, Urlup uses the
operating system's keyring/keychain functionality to get a user name and
password.  If the information does not exist from a previous run of Urlup, it
will query the user interactively for the user name and password, and (unless
the -X or /X argument is given) store them in the user's keyring/keychain so
that it does not have to ask again in the future.  It is also possible to
supply the information directly on the command line using the -u and -p
options (or /u and /p on Windows), but this is discouraged because it is
insecure on multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last time
and the wrong credentials were stored in the keyring/keychain system), add the
-R (or /R on Windows) command-line argument to a command.  The next time
Urlup needs to use a proxy login, it will query for the user name and password
again even if an entry already exists in the keyring or keychain.

Currently, the use of only a single EZProxy proxy is supported.

Connections can be optionally passed session cookie values on the command
line using the -c (or /c on Windows) argument.  The argument should be
followed by a list of key=value pairs separated by commas without spaces.
Example: "acookie=avalue,anothercookie=anothervalue".

This program will print information to the terminal as it processes URLs,
unless the option -q (or /q on Windows) is given to make it more quiet.
'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color
    use_keyring = not no_keyring

    # Some user interactions change depending on the current platform.
    on_windows = sys.platform.startswith('win')

    # Process arguments
    if version:
        print('{} version {}'.format(urlup.__title__, urlup.__version__))
        print('Author: {}'.format(urlup.__author__))
        print('URL: {}'.format(urlup.__url__))
        print('License: {}'.format(urlup.__license__))
        sys.exit()
    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    if input == 'F' and not path.exists('F'):
        input = None
    if output == 'R':
        output = None
    if user == 'U':
        user = None
    if pswd == 'P':
        pswd = None
    if on_windows:
        get_help = '(Hint: use /h to get help.)'
    else:
        get_help = '(Hint: use -h to get help.)'
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
    if cookies:
        cookies = dictify_cookie_list(cookies)

    # General sanity checks.
    if not network_available():
        raise SystemExit(color('No network', 'error', colorize))

    # Let's do this thing.
    ulist = []
    results = []
    try:
        if input:
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
                ulist = map(str.rstrip, f.readlines())
        else:
            # Not given a file.  Do the arguments look like URLs?
            parts = urisplit(url[0])
            if not parts.scheme and not parts.path:
                raise SystemExit(color('{} does not appear to be a URL'.format(url[0]),
                                       'error', colorize))
            ulist = url
        results = updated_urls(ulist, cookies, {}, user, pswd, use_keyring,
                               reset, quiet, explain, colorize)

        if not results:
            msg('No results returned.')
            sys.exit()
        elif output:
            if not quiet:
                msg('Writing CSV file {}'.format(output))
            with open(output, 'w', newline='') as out:
                csvwriter = csv.writer(out, delimiter=',')
                if not isinstance(results, list):
                    results = [results]
                for data in results:
                    if data:
                        csvwriter.writerow([data.original, data.final or '',
                                            data.status, data.error or ''])
        elif quiet:
            # Rationale for the sense of the test against the "quiet" argument:
            # If we were being quiet, no other info will be printed.  Conversely,
            # if we weren't being quiet, then the following would be redundant.
            msg('Results:')
            if not isinstance(results, list):
                results = [results]
            for item in filter(None, results):
                if item.error:
                    msg('Encountered error {} dereferencing {}'
                        .format(item.error, item.original), 'error', colorize)
                elif not item.final:
                    msg('Could not dereference {}'.format(item.original),
                        'warn', colorize)
                else:
                    msg('{} => {}'.format(color(item.original, 'info', colorize),
                                          color(item.final, 'info', colorize)))
            msg('Done.')
    except KeyboardInterrupt:
        msg('Quitting.')


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


def dictify_cookie_list(cookie_list):
    cookies = {}
    for pair in cookie_list.split(','):
        kv = pair.split('=')
        cookies[kv[0]] = kv[1]
    return cookies


def network_available():
    '''Return True if it appears we have a network connection, False if not'''
    try:
        r = requests.get("https://www.caltech.edu")
        return True
    except requests.ConnectionError:
        return False


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
