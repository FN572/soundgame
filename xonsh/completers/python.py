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
        "else",
        "for ",
        "if ",
        "in ",
        "is ",
        "lambda ",
        "not ",
        "or ",
        "+",
        "-",
        "/",
        "//",
        "%",
        "**",
        "|",
        "&",
        "~",
        "^",
        ">>",
        "<<",
        "<",
        "<=",
        ">",
        ">=",
        "==",
        "!=",
        ",",
        "?",
        "??",
        "$(",
        "${",
        "$[",
        "...",
        "![",
        "!(",
        "@(",
        "@$(",
        "@",
    }


@xl.lazyobject
def XONSH_STMT_TOKENS():
    return {
        "as ",
        "assert ",
        "break",
        "class ",
        "continue",
        "def ",
        "del ",
        "elif ",
        "except ",
        "finally:",
        "from ",
        "global ",
        "import ",
        "nonlocal ",
        "pass",
        "raise ",
        "return ",
        "try:",
        "while ",
        "with ",
        "yield ",
        "-",
        "/",
        "//",
        "%",
        "**",
        "|",
        "&",
        "~",
        "^",
        ">>",
        "<<",
        "<",
        "<=",
        "->",
        "=",
        "+=",