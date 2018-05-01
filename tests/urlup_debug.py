#!/usr/bin/env python3
# =============================================================================
# @file    urlup_debug.py
# @brief   Run urlup with debug enabled
# @author  Michael Hucka <mhucka@caltech.edu>
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/urlup
# =============================================================================

import os
import sys
import plac

# Allow this program to be executed directly from the 'tests' directory.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(level=logging.DEBUG, format='')

import urlup
from urlup.__main__ import main as main
plac.call(main)
