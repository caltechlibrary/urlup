@ECHO off
REM ===========================================================================
REM @file    make.bat
REM @brief   Build a .exe using PyInstaller
REM @author  Michael Hucka <mhucka@caltech.edu>
REM @license Please see the file named LICENSE in the project directory
REM @website https://github.com/caltechlibrary/martian
REM
REM Usage:
REM   1. start a terminal shell (e.g., cmd.exe)
REM   2. cd into this directory
REM   3. run "make.bat"
REM ===========================================================================

ECHO Removing "dist" and "build" subdirectories.

RD /S /Q dist build

ECHO Generating InnoSetup script.

python dev/installers/windows/substitute_version.py

ECHO Starting PyInstaller ...

pyinstaller --clean pyinstaller-win32.spec

ECHO "make.bat" finished.
ECHO The .exe will be in the "dist" subdirectory.
