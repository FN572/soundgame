"""Completers for Python code"""
import re
import sys
import inspect
import builtins
import importlib
import collections.abc as cabc

import xonsh.tools as xt
import xonsh.lazyasd as xl

from xonsh.completers.tools import get_filter_function


@xl.lazyobject
def RE_ATTR():
    return re.compile(r"([^\s\(\)]+(\.[^\s\(\)]+)*)\.(\w*)$")


@xl.lazyobject
def XONSH_EXPR_TOKENS():
    return {
        "and ",
        "els