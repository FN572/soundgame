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
        "-=",
        "*=",
        "/=",
        "%=",
        "**=",
        ">>=",
        "<<=",
        "&=",
        "^=",
        "|=",
        "//=",
        ";",
        ":",
        "..",
    }


@xl.lazyobject
def XONSH_TOKENS():
    return set(XONSH_EXPR_TOKENS) | set(XONSH_STMT_TOKENS)


def complete_python(prefix, line, start, end, ctx):
    """
    Completes based on the contents of the current Python environment,
    the Python built-ins, and xonsh operators.
    If there are no matches, split on common delimiters and try again.
    """
    rtn = _complete_python(prefix, line, start, end, ctx)
    if not rtn:
        prefix = (
            re.split(r"\(|=|{|\[|,", prefix)[-1]
            if not prefix.startswith(",")
            else prefix
        )
        start = line.find(prefix)
        rtn = _complete_python(prefix, line, start, end, ctx)
        return rtn, len(prefix)
    return rtn


def _complete_python(prefix, line, start, end, ctx):
    """
    Completes based on the contents of the current Python environment,
    the Python built-ins, and xonsh operators.
    """
    if 