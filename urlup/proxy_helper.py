'''
proxy_helper: a class to help deal with proxy systems

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import requests
import urlup
from urlup.credentials import get_credentials, save_credentials, obtain_credentials

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


# Class definitions.
# .............................................................................

class ProxyHelper():
    _use_keyring = True
    _user = None
    _pswd = None
    _auth_data = {}

    def __init__(self, proxy_user, proxy_pswd, use_keyring):
        self._user = proxy_user
        self._pswd = proxy_pswd
        self._use_keyring = use_keyring
        if __debug__: log('Initizlied proxy helper with user {}, password {}'
                          .format(proxy_user, proxy_pswd))


    def authenticate_proxy(self, url):
        # Get credentials and connect to the proxy, and construct an object we
        # use for subsequent network requests.
        proxy_host = self.proxy_host_from_url(url)
        if __debug__: log('Authenticating to proxy host {}'.format(proxy_host))
        if not self._user or not self._pswd:
            if __debug__: log('Getting credentials from keyring')
            (self._user, self._pswd, _, _) = obtain_credentials(
                _KEYRING, "Proxy login", self._user, self._pswd)
        if self._use_keyring:
            # Save the credentials if they're different from what's currently saved.
            (s_user, s_pswd, _, _) = get_credentials(_KEYRING)
            if s_user != self._user or s_pswd != self._pswd:
                if __debug__: log('Saving credentials to keyring')
                save_credentials(_KEYRING, self._user, self._pswd)
        # FIXME the rest of this is too specific to EZProxy
        credentials = {
            'user': self._user,
            'pass': self._pswd,
        }
        login_url = proxy_host + '/login'
        auth = requests.post(login_url, data = credentials, allow_redirects = False)
        if __debug__: log('Proxy requests response code {}'.format(auth.status_code))
        if 200 <= auth.status_code <= 400:
            self._auth_data[proxy_host] = auth
        else:
            # Not sure what to do here.
            import pdb; pdb.set_trace()


    def cookies(self, url):
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
