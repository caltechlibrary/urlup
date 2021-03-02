# -*- mode: python -*-
# =============================================================================
# @file    pyinstaller-darwin.spec
# @brief   Spec file for PyInstaller for macOS
# @author  Michael Hucka
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/urlup
# =============================================================================

import imp
import os
from   PyInstaller.utils.hooks import copy_metadata
import sys

# I don't know why, but on Windows, the binary can't find humanize at run
# time even if I put it in hiddenimports.  Adding it here solved it.
data_files = copy_metadata('uritools')

configuration = Analysis(['urlup/__main__.py'],
                         pathex = ['.'],
                         binaries = [],
                         datas = data_files,
                         hiddenimports = ['keyring.backends.OS_X', 'wx._html',
                                          'wx._xml'],
                         hookspath = [],
                         runtime_hooks = [],
                         # For reasons I can't figure out, PyInstaller tries
                         # to load these even though they're never imported
                         # by the Urlup code.  Have to exclude them manually.
                         excludes = ['PyQt4', 'PyQt5', 'gtk', 'matplotlib',
                                     'numpy'],
                         win_no_prefer_redirects = False,
                         win_private_assemblies = False,
                         cipher = None,
                        )

application_pyz    = PYZ(configuration.pure,
                         configuration.zipped_data,
                         cipher = None,
                        )

executable         = EXE(application_pyz,
                         configuration.scripts,
                         configuration.binaries,
                         configuration.zipfiles,
                         configuration.datas,
                         name = 'urlup',
                         debug = False,
                         strip = False,
                         upx = True,
                         runtime_tmpdir = None,
                         console = False,
                        )
