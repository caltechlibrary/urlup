'''
errors.py: exceptions defined by Urlup
'''

class NetworkError(Exception):
    '''Class of Urlup exceptions involving network operations.'''
    pass

class ProxyException(Exception):
    '''Class of exceptions related to handling proxies.'''
    pass

class ProxyLoginError(ProxyException):
    '''Could not log in to designated proxy host.'''
    pass
