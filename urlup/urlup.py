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
from   itertools import tee
import os
import requests
import socket
import sys
import textwrap
from   time import time, sleep
from   urllib.parse import urlsplit, quote_plus
from   urllib.request import urlopen, Request

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import urlup
from urlup.messages import color, msg
from urlup.http_code import code_meaning
from urlup.credentials import get_credentials, save_credentials, obtain_credentials
from urlup.errors import ProxyException
from urlup.proxy_helper import ProxyHelper

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


# Data type definitions.
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

def updated_urls(urls, proxy_user = None, proxy_pswd = None, use_keyring = True,
                 quiet = True, explain = False, colorize = False):
    '''Update one URL or a list of URLs.  If given a single URL, it returns a
    single tuple of the following form:
       (old URL, new URL, http status code, error)
    If given a list of URLs, it returns a list of tuples of the same form.
    '''
    proxy_helper = ProxyHelper(proxy_user, proxy_pswd, use_keyring)
    if isinstance(urls, (list, tuple, Iterable)) and not isinstance(urls, str):
        return [_url_data(url, proxy_helper, quiet, explain, colorize) for url in urls]
    else:
        return _url_data(urls, proxy_helper, quiet, explain, colorize)


def _url_data(url, proxy_helper, quiet = True, explain = False, colorize = False):
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
            (old, new, code, url_error) = _followed_url(url, proxy_helper)
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


def _followed_url(url, proxy_helper):
    if __debug__: log('Looking up {}'.format(url))
    starting_url = url
    parts, valid = url_parts(url)
    if not valid:
        return (url, None, None, "Malformed URL")

    # Connect to the host.
    try:
        if proxy_helper.url_contains_proxy(starting_url):
            if __debug__: log('URL uses a proxy: {}'.format(starting_url))
            real_url = proxy_helper.proxied_url(starting_url)
            cookies = proxy_helper.cookies(starting_url)
            conn = requests.post(real_url, cookies = cookies)
            code = conn.status_code
            ending_url = conn.url
        else:
            if __debug__: log('URL has no proxy -- going straight to it')
            conn = http_connection(parts)
            conn.request("GET", starting_url)
            code = conn.getresponse().status
            if code < 300:
                ending_url = conn.getresponse().headers['Location']
            else: # We handle redirections & errors later below.
                ending_url = starting_url
    except socket.gaierror as err:        # gai stands for getaddrinfo()
        if err.errno == 8:
            return (starting_url, None, None, "Cannot resolve host name")
        else:
            return (starting_url, None, None, str(err))
    except http.client.InvalidURL as err:
        # Docs for HTTPResponse say this is raised if port part is bad.
        return (starting_url, None, None, "Bad port")
    except Exception as err:
        if __debug__: log('Error accessing {}: {}'.format(starting_url, str(err)))
        raise

    # Interpret the response.
    if __debug__: log('Got response code {} for {}'.format(code, starting_url))
    if code == 200:
        return (url, ending_url, code, None)
    elif code == 202:
        # Code 202 = Accepted, "received but not yet acted upon."
        if __debug__: log('Pausing & trying')
        sleep(1)                        # Arbitrary.
        final_data = _followed_url(starting_url, proxy_helper) # Try again.
        # Return the original response code, not the subsequent one.
        return (url, final_data[1], code, None)
    elif code in [301, 302, 303, 308]:
        # Redirected.  Note: I previously followed the redirections manually
        # by using the 'Location' http header, but then ran into this value:
        # https://ieeexplore.ieee.orghttp://ieeexplore.ieee.org/xpl/conhome.jsp?punumber=1000245
        # i.e., a mangled value for the 'Location' header.  I gave up and used
        # urlopen instead, which seems to deal with the situation better.
        try:
            # Setting the user agent is because Proquest.com returns a 403
            # otherwise, possibly as an attempt to block automated scraping.
            # Changing the user agent to a browser name seems to solve it.
            r_url = Request(ending_url, headers = {"User-Agent" : "Mozilla/5.0"})
            redirected = urlopen(r_url)
        except Exception as err:
            return (url, None, err.code, str(err))
        new_url = redirected.geturl()
        if __debug__: log('Redirected to {}'.format(new_url))
        return (url, new_url, code, None)
    else:
        return (url, None, code, "Unable to resolve URL")


# Misc. utilities
# .............................................................................

def http_connection(parts):
    if parts.scheme == 'https':
        return http.client.HTTPSConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)
    else:
        return http.client.HTTPConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)


def url_parts(url):
    # Returns two values: a SplitResult value (from urllib) and a Boolean
    parts = urlsplit(url)
    # Do some sanity checking.
    if not parts.netloc:
        if not parts.scheme and not parts.path:
            return (parts, False)
        elif parts.path and not parts.scheme:
            # Most likely case is the user typed a host or domain name only
            starting_url = 'http://' + parts.path
            if __debug__: log('Rewrote {} to {}'.format(url, starting_url))
            parts = urlsplit(starting_url)
            if not parts.netloc:
                return (parts, False)
    return (parts, True)


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
