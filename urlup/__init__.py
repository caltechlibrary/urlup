'''
urlup: Find the ultimate destination for URLs after following redirections.

Authors
-------

Michael Hucka <mhucka@caltech.edu>

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This open-source
software is made freely available under the terms specified in the LICENSE file
provided with this software.
'''

from .__version__ import __version__, __title__, __description__, __url__
from .__version__ import __author__, __email__
from .__version__ import __license__, __copyright__

# Main modules.
from .urlup import updated_urls

# Supporting modules.
from .messages import msg, color
from .http_code import code_meaning
