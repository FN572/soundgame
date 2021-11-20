"""Tools for caching xonsh code."""
import os
import sys
import hashlib
import marshal
import builtins

from xonsh import __version__ as XONSH_VERSION
from xonsh.lazyasd import lazyobject
from xonsh.platform import PYTHON_VERSION_INFO_BYTES


def _splitpath(path, sofar=[]):
    folder, path = os.path.split(path)
    if path == "":
        return sofar[::-1]
    elif folder == "":
        return (sofar + [