# -*- coding: utf-8 -*-
"""Tools to open ``*.py`` files as Unicode.

Uses the encoding specified within the file, as per PEP 263.

Much of the code is taken from the tokenize module in Python 3.2.

This file was forked from the IPython project:

* Copyright (c) 2008-2014, IPython Development Team
* Copyright (C) 2001-2007 Fernando Perez <fperez@colorado.edu>
* Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
* Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
"""
import io
import re

from xonsh.lazyasd import LazyObject
from xonsh.tokenize import detect_encoding, tokopen


cookie_comment_re = LazyObject(
    lambda: re.compile(r"^\s*#.*coding[:=]\s*([-\w.]+)", re.UNICODE),
    globals(),
    "cookie_comment_re",
)


def source_to_unicode(txt, errors="replace", skip_encoding_cookie=True):
    """Converts a bytes string with python source code to unicode.

    Unicode strings are passed through unchanged. Byte strings are checked
    for the python source file encoding cookie to determine encoding.
    txt can be either a bytes buffer or a string containing the source
    code.
    """
    if isinstance(txt, str):
        return txt
    if isinstance(txt, bytes):
        buf = io.BytesIO(txt)
    else:
        buf = txt
