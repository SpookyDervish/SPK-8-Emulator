"""Utility module for the SPK-8 emulator. Includes random helper functions.
"""

import sys
import os


def clear():
    platforms = {
        'linux1' : 'Linux',
        'linux2' : 'Linux',
        'darwin' : 'OS X',
        'win32' : 'Windows'
    }

    if sys.platform == "linux1" or sys.platform == "linux2" or sys.platform == "darwin":
        os.system("clear")
    elif sys.platform == "win32":
        os.system("cls")
    else:
        print("ERR: Unkown operating system")