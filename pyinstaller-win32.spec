# -*- mode: python -*-
# =============================================================================
# @file    pyinstaller-win32.spec
# @brief   Spec file for PyInstaller for Windows
# @author  Michael Hucka
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/urlup
# =============================================================================

import imp
import os
import platform
from   PyInstaller.utils.hooks import copy_metadata
import sys

# I don't know why, but on Windows, the binary can't find humanize at run
# time even if I put it in hiddenimports.  Adding it here solved it.
data_files = copy_metadata('uritools')

configuration = Analysis([r'urlup\__main__.py'],
                         pathex = ['.'],
                         binaries = [],
                         datas = data_files,
                         hiddenimports = ['wx._html', 'wx._xml',
                                          'win32timezone', 'winreg'],
                         hookspath = [],
                         runtime_hooks = [],
                         excludes = [],
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
                         name = 'Urlup',
                         debug = False,
                         strip = False,
                         upx = True,
                         runtime_tmpdir = None,
                         console = True,
                        )
