
# -*- coding: utf-8 -*-
"""Misc. xonsh tools.

The following implementations were forked from the IPython project:

* Copyright (c) 2008-2014, IPython Development Team
* Copyright (C) 2001-2007 Fernando Perez <fperez@colorado.edu>
* Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
* Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>

Implementations:

* decode()
* encode()
* cast_unicode()
* safe_hasattr()
* indent()

"""
import builtins
import collections
import collections.abc as cabc
import contextlib
import ctypes
import datetime
from distutils.version import LooseVersion
import functools
import glob
import itertools
import os
import pathlib
import re
import subprocess
import sys
import threading
import traceback
import warnings
import operator
import ast
import string

# adding imports from further xonsh modules is discouraged to avoid circular
# dependencies
from xonsh import __version__
from xonsh.lazyasd import LazyObject, LazyDict, lazyobject
from xonsh.platform import (
    scandir,
    DEFAULT_ENCODING,
    ON_LINUX,
    ON_WINDOWS,
    PYTHON_VERSION_INFO,
    expanduser,
    os_environ,
)


@functools.lru_cache(1)
def is_superuser():
    if ON_WINDOWS:
        rtn = ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        rtn = os.getuid() == 0
    return rtn


class XonshError(Exception):
    pass


class XonshCalledProcessError(XonshError, subprocess.CalledProcessError):
    """Raised when there's an error with a called process

    Inherits from XonshError and subprocess.CalledProcessError, catching
    either will also catch this error.

    Raised *after* iterating over stdout of a captured command, if the
    returncode of the command is nonzero.

    Example:
        try:
            for line in !(ls):
                print(line)
        except subprocess.CalledProcessError as error:
            print("Error in process: {}.format(error.completed_command.pid))

    This also handles differences between Python3.4 and 3.5 where
    CalledProcessError is concerned.
    """

    def __init__(
        self, returncode, command, output=None, stderr=None, completed_command=None
    ):
        super().__init__(returncode, command, output)
        self.stderr = stderr
        self.completed_command = completed_command


def expand_path(s, expand_user=True):
    """Takes a string path and expands ~ to home if expand_user is set
    and environment vars if EXPAND_ENV_VARS is set."""
    session = getattr(builtins, "__xonsh__", None)
    env = os_environ if session is None else getattr(session, "env", os_environ)
    if env.get("EXPAND_ENV_VARS", False):
        s = expandvars(s)
    if expand_user:
        # expand ~ according to Bash unquoted rules "Each variable assignment is
        # checked for unquoted tilde-prefixes immediately following a ':' or the
        # first '='". See the following for more details.
        # https://www.gnu.org/software/bash/manual/html_node/Tilde-Expansion.html
        pre, char, post = s.partition("=")
        if char:
            s = expanduser(pre) + char
            s += os.pathsep.join(map(expanduser, post.split(os.pathsep)))
        else:
            s = expanduser(s)
    return s


def _expandpath(path):
    """Performs environment variable / user expansion on a given path
    if EXPAND_ENV_VARS is set.
    """
    session = getattr(builtins, "__xonsh__", None)
    env = os_environ if session is None else getattr(session, "env", os_environ)
    expand_user = env.get("EXPAND_ENV_VARS", False)
    return expand_path(path, expand_user=expand_user)


def decode_bytes(b):
    """Tries to decode the bytes using XONSH_ENCODING if available,
    otherwise using sys.getdefaultencoding().
    """
    session = getattr(builtins, "__xonsh__", None)
    env = os_environ if session is None else getattr(session, "env", os_environ)
    enc = env.get("XONSH_ENCODING") or DEFAULT_ENCODING
    err = env.get("XONSH_ENCODING_ERRORS") or "strict"
    return b.decode(encoding=enc, errors=err)


def findfirst(s, substrs):
    """Finds whichever of the given substrings occurs first in the given string
    and returns that substring, or returns None if no such strings occur.
    """
    i = len(s)
    result = None
    for substr in substrs:
        pos = s.find(substr)
        if -1 < pos < i:
            i = pos
            result = substr
    return i, result


class EnvPath(cabc.MutableSequence):
    """A class that implements an environment path, which is a list of
    strings. Provides a custom method that expands all paths if the
    relevant env variable has been set.
    """

    def __init__(self, args=None):
        if not args:
            self._l = []
        else:
            if isinstance(args, str):
                self._l = args.split(os.pathsep)
            elif isinstance(args, pathlib.Path):
                self._l = [args]
            elif isinstance(args, bytes):
                # decode bytes to a string and then split based on
                # the default path separator
                self._l = decode_bytes(args).split(os.pathsep)
            elif isinstance(args, cabc.Iterable):
                # put everything in a list -before- performing the type check
                # in order to be able to retrieve it later, for cases such as
                # when a generator expression was passed as an argument
                args = list(args)
                if not all(isinstance(i, (str, bytes, pathlib.Path)) for i in args):
                    # make TypeError's message as informative as possible
                    # when given an invalid initialization sequence
                    raise TypeError(
                        "EnvPath's initialization sequence should only "
                        "contain str, bytes and pathlib.Path entries"
                    )
                self._l = args
            else:
                raise TypeError(
                    "EnvPath cannot be initialized with items "
                    "of type %s" % type(args)
                )

    def __getitem__(self, item):
        # handle slices separately
        if isinstance(item, slice):
            return [_expandpath(i) for i in self._l[item]]
        else:
            return _expandpath(self._l[item])

    def __setitem__(self, index, item):
        self._l.__setitem__(index, item)

    def __len__(self):
        return len(self._l)

    def __delitem__(self, key):
        self._l.__delitem__(key)

    def insert(self, index, value):
        self._l.insert(index, value)

    @property
    def paths(self):
        """
        Returns the list of directories that this EnvPath contains.
        """
        return list(self)

    def __repr__(self):
        return repr(self._l)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return all(map(operator.eq, self, other))

    def _repr_pretty_(self, p, cycle):
        """ Pretty print path list """
        if cycle:
            p.text("EnvPath(...)")
        else:
            with p.group(1, "EnvPath(\n[", "]\n)"):
                for idx, item in enumerate(self):
                    if idx:
                        p.text(",")
                        p.breakable()
                    p.pretty(item)

    def __add__(self, other):
        if isinstance(other, EnvPath):
            other = other._l
        return EnvPath(self._l + other)

    def __radd__(self, other):
        if isinstance(other, EnvPath):
            other = other._l
        return EnvPath(other + self._l)

    def add(self, data, front=False, replace=False):
        """Add a value to this EnvPath,

        path.add(data, front=bool, replace=bool) -> ensures that path contains data, with position determined by kwargs

        Parameters
        ----------
        data : string or bytes or pathlib.Path
            value to be added
        front : bool
            whether the value should be added to the front, will be
            ignored if the data already exists in this EnvPath and
            replace is False
            Default : False
        replace : bool
            If True, the value will be removed and added to the
            start or end(depending on the value of front)
            Default : False

        Returns
        -------
        None

        """
        if data not in self._l:
            self._l.insert(0 if front else len(self._l), data)
        elif replace:
            self._l.remove(data)
            self._l.insert(0 if front else len(self._l), data)


@lazyobject
def FORMATTER():
    return string.Formatter()


class DefaultNotGivenType(object):
    """Singleton for representing when no default value is given."""

    __inst = None

    def __new__(cls):
        if DefaultNotGivenType.__inst is None:
            DefaultNotGivenType.__inst = object.__new__(cls)
        return DefaultNotGivenType.__inst


DefaultNotGiven = DefaultNotGivenType()

BEG_TOK_SKIPS = LazyObject(
    lambda: frozenset(["WS", "INDENT", "NOT", "LPAREN"]), globals(), "BEG_TOK_SKIPS"
)
END_TOK_TYPES = LazyObject(
    lambda: frozenset(["SEMI", "AND", "OR", "RPAREN"]), globals(), "END_TOK_TYPES"
)
RE_END_TOKS = LazyObject(
    lambda: re.compile(r"(;|and|\&\&|or|\|\||\))"), globals(), "RE_END_TOKS"
)
LPARENS = LazyObject(
    lambda: frozenset(
        ["LPAREN", "AT_LPAREN", "BANG_LPAREN", "DOLLAR_LPAREN", "ATDOLLAR_LPAREN"]
    ),
    globals(),
    "LPARENS",
)


def _is_not_lparen_and_rparen(lparens, rtok):
    """Tests if an RPAREN token is matched with something other than a plain old
    LPAREN type.
    """
    # note that any([]) is False, so this covers len(lparens) == 0
    return rtok.type == "RPAREN" and any(x != "LPAREN" for x in lparens)


def balanced_parens(line, mincol=0, maxcol=None, lexer=None):
    """Determines if parentheses are balanced in an expression."""
    line = line[mincol:maxcol]
    if lexer is None:
        lexer = builtins.__xonsh__.execer.parser.lexer
    if "(" not in line and ")" not in line:
        return True
    cnt = 0
    lexer.input(line)
    for tok in lexer:
        if tok.type in LPARENS:
            cnt += 1
        elif tok.type == "RPAREN":
            cnt -= 1
        elif tok.type == "ERRORTOKEN" and ")" in tok.value:
            cnt -= 1
    return cnt == 0


def find_next_break(line, mincol=0, lexer=None):
    """Returns the column number of the next logical break in subproc mode.
    This function may be useful in finding the maxcol argument of
    subproc_toks().
    """
    if mincol >= 1:
        line = line[mincol:]
    if lexer is None:
        lexer = builtins.__xonsh__.execer.parser.lexer
    if RE_END_TOKS.search(line) is None:
        return None
    maxcol = None
    lparens = []
    lexer.input(line)
    for tok in lexer:
        if tok.type in LPARENS:
            lparens.append(tok.type)
        elif tok.type in END_TOK_TYPES:
            if _is_not_lparen_and_rparen(lparens, tok):
                lparens.pop()
            else:
                maxcol = tok.lexpos + mincol + 1
                break
        elif tok.type == "ERRORTOKEN" and ")" in tok.value:
            maxcol = tok.lexpos + mincol + 1
            break
        elif tok.type == "BANG":
            maxcol = mincol + len(line) + 1
            break
    return maxcol


def _offset_from_prev_lines(line, last):
    lines = line.splitlines(keepends=True)[:last]
    return sum(map(len, lines))


def subproc_toks(
    line, mincol=-1, maxcol=None, lexer=None, returnline=False, greedy=False
):
    """Encapsulates tokens in a source code line in a uncaptured
    subprocess ![] starting at a minimum column. If there are no tokens
    (ie in a comment line) this returns None. If greedy is True, it will encapsulate
    normal parentheses. Greedy is False by default.
    """
    if lexer is None:
        lexer = builtins.__xonsh__.execer.parser.lexer
    if maxcol is None:
        maxcol = len(line) + 1
    lexer.reset()
    lexer.input(line)
    toks = []
    lparens = []
    saw_macro = False
    end_offset = 0
    for tok in lexer:
        pos = tok.lexpos
        if tok.type not in END_TOK_TYPES and pos >= maxcol:
            break
        if tok.type == "BANG":
            saw_macro = True
        if saw_macro and tok.type not in ("NEWLINE", "DEDENT"):
            toks.append(tok)
            continue
        if tok.type in LPARENS:
            lparens.append(tok.type)
        if greedy and len(lparens) > 0 and "LPAREN" in lparens:
            toks.append(tok)
            if tok.type == "RPAREN":
                lparens.pop()
            continue
        if len(toks) == 0 and tok.type in BEG_TOK_SKIPS:
            continue  # handle indentation
        elif len(toks) > 0 and toks[-1].type in END_TOK_TYPES:
            if _is_not_lparen_and_rparen(lparens, toks[-1]):
                lparens.pop()  # don't continue or break
            elif pos < maxcol and tok.type not in ("NEWLINE", "DEDENT", "WS"):
                if not greedy:
                    toks.clear()
                if tok.type in BEG_TOK_SKIPS:
                    continue
            else:
                break
        if pos < mincol:
            continue
        toks.append(tok)
        if tok.type == "WS" and tok.value == "\\":
            pass  # line continuation
        elif tok.type == "NEWLINE":
            break
        elif tok.type == "DEDENT":
            # fake a newline when dedenting without a newline
            tok.type = "NEWLINE"
            tok.value = "\n"
            tok.lineno -= 1
            if len(toks) >= 2:
                prev_tok_end = toks[-2].lexpos + len(toks[-2].value)
            else:
                prev_tok_end = len(line)
            if "#" in line[prev_tok_end:]:
                tok.lexpos = prev_tok_end  # prevents wrapping comments
            else:
                tok.lexpos = len(line)
            break
        elif check_bad_str_token(tok):
            return
    else:
        if len(toks) > 0 and toks[-1].type in END_TOK_TYPES:
            if _is_not_lparen_and_rparen(lparens, toks[-1]):
                pass