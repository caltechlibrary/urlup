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

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
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
import urllib3.exceptions
import validators

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import urlup
from urlup.messages import color, msg
from urlup.http_code import code_meaning
from urlup.credentials import get_credentials, save_credentials, obtain_credentials
from urlup.errors import NetworkError, ProxyLoginError, ProxyException
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

def updated_urls(urls, cookies = {}, headers = {},
                 proxy_user = None, proxy_pswd = None,
                 use_keyring = True, reset = False,
                 quiet = True, explain = False, colorize = False):
    '''Update one URL or a list of URLs.  If given a single URL, it returns a
    single tuple of the following form:
       (old URL, new URL, http status code, error)
    If given a list of URLs, it returns a list of tuples of the same form.
    '''
    helper = ProxyHelper(proxy_user, proxy_pswd, use_keyring, reset)
    if isinstance(urls, (list, tuple, Iterable)) and not isinstance(urls, str):
        return [_url_data(url, cookies, headers, helper, quiet, explain, colorize)
                for url in urls]
    else:
        return _url_data(urls, cookies, headers, helper, quiet, explain, colorize)


def _url_data(url, cookies, headers, proxy_helper, quiet, explain, colorize):
    '''Update one URL and return a tuple of (old URL, new URL).'''
    url = url.strip()
    if not url:
        return ()
    retry = True
    failures = 0
    sleep_time = 2
    while retry and failures < _MAX_RETRIES:
        retry = False
        error = None
        try:
            (old, new, code, error) = _analysis(url, cookies, headers, proxy_helper)
            if not quiet:
                if error:
                    msg('{} -- {}'.format(url, color(error, 'error', colorize)))
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
            return UrlData(old, new, code, error)
        except requests.exceptions.ConnectTimeout as err:
            if not quiet:
                msg('{} connection timed out'.format(url), 'error', colorize)
            return UrlData(url, None, None, 'Timed out trying to connect')
        except Exception as err:
            # If we fail, try again in case it's actually due to a network issue
            if __debug__: log('{}: {}', url, err)
            failures += 1
            if not quiet:
                msg('{} connection attempt failed: {}'.format(url, err), 'warn', colorize)
                msg('Retrying in {}s ...'.format(sleep_time), 'warn', colorize)
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


def _analysis(url, cookies, headers, proxy_helper):
    if __debug__: log('Looking up {}'.format(url))
    starting_url = normalized_url(url)
    if not starting_url:
        return (url, None, None, 'Malformed URL')

    # Connect to the host.
    cookie_jar = None
    using_proxy = False
    try:
        if proxy_helper.url_contains_proxy(starting_url):
            if __debug__: log('URL uses a proxy: {}'.format(starting_url))
            using_proxy = True
            real_url = proxy_helper.proxied_url(starting_url)
            cookie_jar = proxy_helper.cookies(starting_url)
            requests.utils.add_dict_to_cookiejar(cookie_jar, cookies)
            conn = requests.get(real_url, cookies = cookie_jar,
                                headers = headers, timeout = _NETWORK_TIMEOUT)
            code = conn.status_code
            ending_url = conn.url
        else:
            if __debug__: log('URL has no proxy -- going straight to it')
            cookie_jar = requests.cookies.RequestsCookieJar()
            requests.utils.add_dict_to_cookiejar(cookie_jar, cookies)
            conn = requests.get(starting_url, cookies = cookie_jar,
                                headers = headers, timeout = _NETWORK_TIMEOUT)
            if conn.history:
                # Redirection occured.  Get the first status code.
                code = conn.history[0].status_code
            else:
                code = conn.status_code
            ending_url = conn.url
    except requests.exceptions.ConnectionError as err:
        if err.args and isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
            # I see different error strings on Windows vs mac.
            serr = str(err)
            if 'not known' in serr or 'getaddrinfo failed' in serr:
                if using_proxy:
                    msg = 'Proxy is unable to resolve the destination host name'
                else:
                    msg = 'Cannot resolve host name'
                return (starting_url, None, None, msg)
            else:
                raise
    except requests.exceptions.InvalidSchema as err:
        return (starting_url, None, None, "Unsupported network protocol")
    except http.client.InvalidURL as err:
        # Docs for HTTPResponse say this is raised if port info is bad.
        if __debug__: log('Bad port in {}: {}'.format(starting_url, str(err)))
        return (starting_url, None, None, "Bad port")
    except (ProxyLoginError, ProxyException, NetworkError) as err:
        if __debug__: log('Proxy error: {}'.format(starting_url, str(err)))
        return (starting_url, None, None, "Proxy login failure")
    except Exception as err:
        if __debug__: log('Error accessing {}: {}'.format(starting_url, str(err)))
        raise

    # Interpret the response.
    if __debug__: log('Got response code {} for {}'.format(code, starting_url))
    if code == 202:
        # Code 202 = Accepted, "received but not yet acted upon."
        if __debug__: log('Pausing & retrying')
        sleep(1)                        # Sleep a short time and try again.
        final_data = _analysis(starting_url, cookies, headers, proxy_helper)
        # Return the original response code, not the subsequent one.
        return (url, final_data[1], code, None)
    elif 200 <= code < 400:
        return (url, ending_url, code, None)
    elif code in [401, 402, 403, 407, 451, 511]:
        return (url, None, code, "Access is forbidden or requires authentication")
    elif code in [404, 410]:
        return (url, None, code, "No content found at this location")
    elif code in [405, 406, 409, 411, 412, 414, 417, 428, 431, 505, 510]:
        return (url, None, code, "Server returned code {} -- please report this".format(code))
    elif code in [415, 416]:
        return (url, None, code, "Server rejected the request")
    elif code == 429:
        return (url, None, code, "Server blocking further requests due to rate limits")
    elif code == 503:
        return (url, None, code, "Server is unavailable -- try again later")
    elif code in [500, 501, 502, 506, 507, 508]:
        return (url, None, code, "Internal server error")
    else:
        return (url, None, code, "Unable to resolve URL")


# Misc. utilities
# .............................................................................

def http_connection(parts):
    if parts.scheme == 'https':
        return http.client.HTTPSConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)
    else:
        return http.client.HTTPConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)


def normalized_url(url):
    # Returns two values: a SplitResult value (from urllib) and a Boolean
    parts = urlsplit(url)
    if parts.netloc:
        if validators.domain(host_from_netloc(parts.netloc)):
            return url
        else:
            return None
    elif not parts.scheme and not parts.path:
        return None
    elif parts.path and not parts.scheme:
        # Most likely case is the user typed a host or domain name only
        starting_url = 'http://' + parts.path
        if __debug__: log('Rewrote {} to {}'.format(url, starting_url))
        parts = urlsplit(starting_url)
        if parts.netloc and validators.domain(host_from_netloc(parts.netloc)):
            return starting_url
        else:
            return None
    return url


def host_from_netloc(nl):
    return nl[:nl.find(':')] if ':' in nl else nl


def severity(code):
    if code < 300:
        return 'info'
    elif code < 400:
        return 'cyan'
    else:
        return 'error'


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
