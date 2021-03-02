'''
proxy_helper: a class to help deal with proxy systems

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import getpass
import requests
import sys
from   time import time, sleep

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import urlup
from urlup.credentials import get_credentials, save_credentials, obtain_credentials
from urlup.errors import NetworkError, ProxyLoginError, ProxyException

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

_KEYRING = "org.caltechlibrary.urlup"
'''
The name of the keyring used to store credentials for a proxy, if any.
'''

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


# Class definitions.
# .............................................................................

class ProxyHelper():
    '''A stateful object to connect to a proxy server and obtain session
    cookies that can be used in subsequent network calls through the proxy.
    '''

    _use_keyring = True
    _user = None
    _pswd = None
    _reset = False
    _auth_data = {}

    def __init__(self, proxy_user, proxy_pswd, use_keyring = True, reset = False):
        '''Initialize a proxy helper.  Parameters 'proxy_user' and 'proxy_pswd'
        are to be used when the user supplies credentials for the proxy host;
        they can be left None, in which case, ProxyHelper will either use
        the keyring/keychain facility or ask the user at the time that the
        method authenticate_proxy() is called.  If 'use_keyring' is False,
        then the keyring/keychain approach is not used.  If 'reset' is True,
        then it will ask the user for a proxy login and password even if it
        already has the information, and will overwrite the information in the
        keyring (unless 'use_keyring' is False).
        '''
        self._user = proxy_user
        self._pswd = proxy_pswd
        self._use_keyring = use_keyring
        self._reset = reset
        if __debug__: log('Initizlied proxy helper with user {}, password {}'
                          .format(proxy_user, proxy_pswd))


    def authenticate_proxy(self, url):
        '''Parameter 'url' should be a full proxied URL.  This method will
        extract the proxy host address from the URL (using patter matching)
        and try to authenticate the user to the proxy host.  The credentials
        that will be used are (1) those provided at initialization, or (2)
        from the system keyring/keychain (unless this was disabled at the
        time this proxy helper was initialized), or (3) by asking the user for
        a login name and password.  This method does not return a value;
        rather, it sets the state in this ProxyHelper object so that the
        calling code can call the 'cookies()' method to get the necessary
        data for subsequent network calls.
        '''
        proxy_host = self.proxy_host_from_url(url)
        if __debug__: log('Authenticating to proxy host {}'.format(proxy_host))
        if not self._user or not self._pswd or self._reset:
            if self._use_keyring and not self._reset:
                if __debug__: log('Getting credentials from keyring')
                self._user, self._pswd, _, _ = obtain_credentials(
                    _KEYRING, "Proxy login", self._user, self._pswd)
            else:
                if self._use_keyring:
                    if __debug__: log('Keyring disabled')
                if self._reset:
                    if __debug__: log('Reset invoked')
                self._user = input('Proxy login: ')
                self._pswd = getpass.getpass('Password for "{}": '.format(self._user))
        if self._use_keyring:
            # Save the credentials if they're different from what's currently saved.
            s_user, s_pswd, _, _ = get_credentials(_KEYRING)
            if s_user != self._user or s_pswd != self._pswd:
                if __debug__: log('Saving credentials to keyring')
                save_credentials(_KEYRING, self._user, self._pswd)

        # Connect to the proxy, with care for potential problems like timeouts.
        # FIXME the rest of this is too specific to EZProxy
        login = proxy_host + '/login'
        data = { 'user': self._user, 'pass': self._pswd }
        retry = True
        failures = 0
        sleep_time = 2
        while retry and failures < _MAX_RETRIES:
            retry = False
            try:
                auth = requests.post(login, data = data, allow_redirects = False,
                                     timeout = _NETWORK_TIMEOUT)
            except requests.exceptions.Timeout:
                if __debug__: log('retrying in {}s', sleep_time)
                failures += 1
                sleep(sleep_time)
                sleep_time *= _SLEEP_FACTOR
                retry = True
            except requests.exceptions.TooManyRedirects:
                # Something is wrong with the URL.
                raise ProxyException('Bad proxy URL: {}'.format(login))
            except requests.exceptions.ConnectionError as err:
                # Network problem (e.g. DNS failure, refused connection, etc).
                raise NetworkError('Failed to connect to {}'.format(login))
            except requests.exceptions.RequestException as err:
                # Catastrophic error.
                raise ProxyException('Fatal error: {}'.format(str(err)))
        if failures >= _MAX_RETRIES:
            raise ProxyException('Unable to connect to {}'.format(proxy_host))

        # Successfully connected to the proxy server. Process the results.
        if __debug__: log('Proxy response code {}'.format(auth.status_code))
        if len(auth.cookies) == 0:
            # No cookies => authentication unsuccessful.
            raise ProxyLoginError('Login incorrect')
        if 200 <= auth.status_code <= 400:
            # Anything in the 200-399 range seems to work out okay.
            self._auth_data[proxy_host] = auth
        else:
            # Something went wrong.
            raise ProxyException('Unable to authenticate to proxy: {}')


    def cookies(self, url):
        '''Return a Python Requests library Cookie object.'''
        if not self.url_contains_proxy(url):
            return {}
        self.authenticate_proxy(url)
        proxy_host = self.proxy_host_from_url(url)
        if proxy_host in self._auth_data:
            return self._auth_data[proxy_host].cookies
        else:
            return {}


    def proxy_host_from_url(self, url):
        '''Extract and return the proxy host part from a URL.'''
        # We expect to see a URL of the form
        #   https://clsproxy.library.caltech.edu/....stuff....
        # We return the first address.
        # Note: 8 is the length of 'https://', which will will work even if we get http
        next_slash = url.find('/', 8)
        return url[:next_slash]


    def proxied_url(self, url):
        '''Return the destination URL buried inside a proxied URL.'''
        # FIXME this is too specific to ezproxy
        start = url.find('url=')
        return url[start + 4:]


    def url_contains_proxy(self, url):
        '''Returns True if the given URL appears to include a proxy part.'''
        return 'proxy' in url


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
