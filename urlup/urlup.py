'''
urlup: find the ultimate destination for URLs after following redirections.

This implements functionality to take a list of URLs and look up their
destinations to find out the final URLs after any redirections that may have
taken place.  It records the original url, final url, and initial http status
code.

Authors
-------

Michael Hucka <mhucka@caltech.edu>

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This open-source
software is made freely available under the terms specified in the LICENSE file
provided with this software.
'''

import http.client
from   http.client import responses as http_responses
import os
import sys
import textwrap
from   time import time, sleep
from   urllib.parse import urlsplit

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

from commonpy import http_code

import urlup
from urlup.messages import color, msg

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

_NETWORK_TIMEOUT = 15
'''
How long to wait on a network connection attempt.
'''

_SLEEP_FACTOR = 2
'''
Each time a failure occurs, this module will wait a while and try again.  The
wait duration increases geometrically by this factor each time.
'''

_MAX_RETRIES = 5
'''
Maximum number of times a network operation is tried before this module stops
trying and exits with an error.
'''


# Main functions.
# .............................................................................

def updated_urls(url_list, colorize = True, quiet = False, verbose = False):
    results = []
    for url in url_list:
        url = url.strip()
        if not url:
            continue
        retry = True
        failures = 0
        sleep_time = 2
        while retry and failures < _MAX_RETRIES:
            retry = False
            try:
                (old, new, code) = url_data(url)
                if not quiet:
                    if verbose:
                        details = '[status code {} = {}]'.format(code,
                            http_code.description(code))
                        text = textwrap.fill(details, initial_indent = '   ',
                                             subsequent_indent = '   ')
                        msg('{} ==> {}\n{}'.format(old, new, text),
                            severity(code), colorize)
                    else:
                        msg('{} ==> {} [{}]'.format(old, new, code),
                            severity(code), colorize)
                results.append((old, new, code))
            except Exception as err:
                # If we fail, try again, in case it's a network interruption
                failures += 1
                if not quiet:
                    msg('{} problem: {}'.format(url, err), 'warn', colorize)
                    msg('Retrying in {}s ...'.format(sleep_time), 'warn', colorize)
                sleep(sleep_time)
                sleep_time *= _SLEEP_FACTOR
                retry = True
    if failures >= _MAX_RETRIES:
        raise SystemExit(color('Exceeded maximum failures. Quitting.'))
    return results


def url_data(url):
    if __debug__: log('Looking up {}'.format(url))
    parts = urlsplit(url)
    if parts.scheme == 'https':
        conn = http.client.HTTPSConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)
    else:
        conn = http.client.HTTPConnection(parts.netloc, timeout=_NETWORK_TIMEOUT)
    conn.request("GET", url, {})
    response = conn.getresponse()
    if __debug__: log('Got response code {}'.format(response.status))
    if response.status == 200:
        return (url, url, response.status)
    elif response.status == 202:
        # Code 202 = Accepted. "The request has been received but not yet
        # acted upon. It is non-committal, meaning that there is no way in
        # HTTP to later send an asynchronous response indicating the outcome
        # of processing the request. It is intended for cases where another
        # process or server handles the request, or for batch processing."
        if __debug__: log('Pausing & trying')
        sleep(1)                        # Arbitrary.
        final_data = url_data(url)
        return (url, final_data[1], response.status)
    elif response.status in [301, 302, 303, 308]:
        # Redirection.  Start from the top with new URL.
        new_url = response.getheader('Location')
        if __debug__: log('New url: {}'.format(new_url))
        final_data = url_data(new_url)
        return (url, final_data[1], response.status)
    else:
        return (url, None, response.status)


# Misc. utilities
# .............................................................................

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
