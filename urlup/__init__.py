'''
urlup: Find the ultimate destination for URLs after following redirections.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from .__version__ import __version__, __title__, __description__, __url__
from .__version__ import __author__, __email__
from .__version__ import __license__, __copyright__

# Main modules.
from .urlup import updated_urls, UrlData

# Supporting modules.
from .messages import msg, color
from .http_code import code_meaning
from .errors import ProxyLoginError, ProxyException, NetworkError
