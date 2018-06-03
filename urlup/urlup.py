'''
urlup: find the ultimate destination for URLs after following redirections.

This implements functionality to take a list of URLs and look up their
destinations to find out the final URLs after any redirections that may have
taken place.  It records the original url, final url, and initial http status
code.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   collections import Iterable, namedtuple
import http.client
from   http.client import responses as http_responses
import os
import socket
import sys
import textwrap
from   time import time, sleep
from   urllib.parse import urlsplit
import urllib.request

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import urlup
from urlup.messages import color, msg
from urlup.http_code import code_meaning

# NOTE: to turn on debugging, make sure python -O was *not* used to start
# python, then set the logging level to DEBUG *before* loading this module.
# Conversely, to optimize out all the debugging code, use python -O or -OO
# and everything inside "if __debug__" blocks will be entirely compiled out.
if __debug__:
    import logging
    logging.basicConfig(level = logging.INFO)
    logger = logging.getLogger('urlup')
    def log(s, *other_args): logger.debug('urlup: ' + s.format(*other_args))


# Global constants.
# .............................................................................

_NETWORK_TIMEOUT = 10
'''
How long to wait on a network connection attempt.
'''

_SLEEP_FACTOR = 2
'''
Each time a failure occurs, this module will wait a while and try again.  The
wait duration increases geometrically by this factor each time.
'''

_MAX_RETRIES = 3
'''
Maximum number of times a network operation is tried before this module stops
trying and exits with an error.
'''


# Global constants.
# .............................................................................

UrlData = namedtuple('UrlData', 'original final status error')
UrlData.__doc__ = '''Data about the eventual destination of a given URL.
  'original' is the starting URL
  'final' is the URL after dereferencing and following redirections
  'status' is the HTTP status code obtained on the 'original' URL
  'error' is the error (if any) encountered while trying to dereference the URL
'''


# Main functions.
# .............................................................................

def updated_urls(urls, headers = None, quiet = True, explain = False, colorize = False):
    '''Update one URL or a list of URLs.  If given a single URL, it returns a
    single tuple of the following form:
       (old URL, new URL, http status code, error)
    If given a list of URLs, it returns a list of tuples of the same form.
    '''
    if isinstance(urls, (list, tuple, Iterable)) and not isinstance(urls, str):
        return [_url_tuple(url, headers, quiet, explain, colorize) for url in urls]
    else:
        return _url_tuple(urls, headers, quiet, explain, colorize)


def _url_tuple(url, headers = None, quiet = True, explain = False, colorize = False):
    '''Update one URL and return a tuple of (old URL, new URL).'''
    url = url.strip()
    if not url:
        return ()
    retry = True
    failures = 0
    error = None
    sleep_time = 2
    while retry and failures < _MAX_RETRIES:
        retry = False
        try:
            (old, new, code, url_error) = _url_data(url, headers)
            if not quiet:
                if url_error:
                    msg('{} -- {}'.format(url, color(url_error, 'error', colorize)))
                elif explain:
                    desc = code_meaning(code)
                    details = '[status code {} = {}]'.format(code, desc)
                    text = textwrap.fill(details, initial_indent = '   ',
                                         subsequent_indent = '   ')
                    msg('{} ==> {}\n{}'.format(color(old, severity(code), colorize),
                                               color(new, severity(code), colorize),
                                               color(text, 'dark', colorize)))
                else:
                    msg('{} ==> {} {}'.format(color(old, severity(code), colorize),
                                                color(new, severity(code), colorize),
                                                color('[' + str(code) + ']', 'dark', colorize)))
            return UrlData(old, new, code, url_error)
        except Exception as err:
            # If we fail, try again, in case it's a network interruption
            if __debug__: log('{}: {}', url, err)
            failures += 1
            error = err
            if not quiet:
                msg('{} problem: {}'.format(url, err), 'warn', colorize)
                msg('Retrying in {}s ...'.format(sleep_time), 'warn', colorize)
            if __debug__: log('retrying in {}s', sleep_time)
            sleep(sleep_time)
            sleep_time *= _SLEEP_FACTOR
            retry = True
    if failures >= _MAX_RETRIES:
        if not quiet:
            if error:
                msg('{}: {}'.format(url, color(error, 'error', colorize)))
            else:
                msg('{}: {}'.format(url, color('Failed', 'error', colorize)))
        return UrlData(url, None, None, error)
    return UrlData(url, None, None, None)


def _url_data(url, headers = None):
    if __debug__: log('Looking up {}'.format(url))
    url_used = url
    parts = urlsplit(url)
    if not parts.netloc:
        if not parts.scheme and not parts.path:
            return (url, None, None, "Malformed URL")
        elif parts.path and not parts.scheme:
            # Most likely case is the user typed a host or domain name only
            url_used = 'http://' + parts.path
            if __debug__: log('Rewrote {} to {}'.format(url, url_used))
            parts = urlsplit(url_used)
    conn = http_connection(parts)
    try:
        conn.request("GET", url_used, headers = (headers or {}))
    except socket.gaierror as err:
        # gai = getaddrinfo()
        if err.errno == 8:
            # "nodename nor servname provided, or not known"
            return (url_used, None, None, "Cannot resolve host name")
        else:
            return (url_used, None, None, err)

    response = conn.getresponse()
    if __debug__: log('Got response code {}'.format(response.status))
    if response.status == 200:
        return (url, url_used, response.status, None)
    elif response.status == 202:
        # Code 202 = Accepted. "The request has been received but not yet
        # acted upon. It is non-committal, meaning that there is no way in
        # HTTP to later send an asynchronous response indicating the outcome
        # of processing the request. It is intended for cases where another
        # process or server handles the request, or for batch processing."
        if __debug__: log('Pausing & trying')
        sleep(1)                        # Arbitrary.
        final_data = _url_data(url_used) # Try again.
        # Return the original response code, not the subsequent one.
        return (url, final_data[1], response.status, None)
    elif response.status in [301, 302, 303, 308]:
        # Redirection.  Start from the top with new URL.
        # Note: I previously used the following to get the new location
        # manually, but then ran into a case where the value returne was
        # https://ieeexplore.ieee.orghttp://ieeexplore.ieee.org/xpl/conhome.jsp?punumber=1000245
        # i.e., it was mangled.  This is hard to detect because it still has
        # the form of a URI, and all the usual utilities just say it's
        # valid, even though it's obviously not.
        # new_url = response.getheader('Location')
        try:
            ref = urllib.request.urlopen(url_used)
        except Exception as err:
            return (url, None, err.status, err)
        new_url = ref.geturl()
        if __debug__: log('Redirected to {}'.format(new_url))
        return (url, new_url, response.status, None)
    else:
        return (url, None, response.status, "Unable to resolve URL")


# Misc. utilities
# .............................................................................

def http_connection(parts):
    if parts.scheme == 'https':
        return http.client.HTTPSConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)
    else:
        return http.client.HTTPConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)


def severity(code):
    if code < 300:
        return 'info'
    elif code < 400:
        return 'blue'
    else:
        return 'error'


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
