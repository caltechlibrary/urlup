#!/usr/bin/env python3
# =============================================================================
# @file    setup.py
# @brief   urlup setup file
# @author  Michael Hucka <mhucka@caltech.edu>
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/urlup
# =============================================================================

import os
from   os import path
from   setuptools import setup
import sys

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'requirements.txt')) as f:
    reqs = f.read().rstrip().splitlines()

# The following reads the variables without doing an "import urlup",
# because the latter will cause the python execution environment to fail if
# any dependencies are not already installed -- negating most of the reason
# we're using setup() in the first place.  This code avoids eval, for security.

version = {}
with open(path.join(here, 'urlup/__version__.py')) as f:
    text = f.read().rstrip().splitlines()
    vars = [line for line in text if line.startswith('__') and '=' in line]
    for v in vars:
        setting = v.split('=')
        version[setting[0].strip()] = setting[1].strip().replace("'", '')

# Finally, define our namesake.

setup(
    name             = version['__title__'].lower(),
    description      = 'Dereference HTTP addresses to determine ultimate destinations',
    long_description = version['__description__'],
    version          = version['__version__'],
    author           = version['__author__'],
    author_email     = version['__email__'],
    license          = version['__license__'],
    url              = version['__url__'],
    download_url     = 'https://github.com/caltechlibrary/urlup/archive/1.5.0.tar.gz',
    keywords         = "http redirects URL",
    packages         = ['urlup'],
    scripts          = ['bin/urlup'],
    install_requires = reqs,
    platforms        = 'any',
    python_requires  = '>=3',
)
