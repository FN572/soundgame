
# -*- coding: utf-8 -*-
"""Interface for running Python functions as subprocess-mode commands.

Code for several helper methods in the `ProcProxy` class have been reproduced
without modification from `subprocess.py` in the Python 3.4.2 standard library.
The contents of `subprocess.py` (and, thus, the reproduced methods) are
Copyright (c) 2003-2005 by Peter Astrand <astrand@lysator.liu.se> and were
licensed to the Python Software foundation under a Contributor Agreement.
"""
import io
import os
import re
import sys
import time
import queue
import array
import ctypes
import signal
import inspect
import builtins
import functools
import threading
import subprocess
import collections.abc as cabc

from xonsh.platform import (
    ON_WINDOWS,
    ON_POSIX,
    ON_MSYS,
    ON_CYGWIN,
    CAN_RESIZE_WINDOW,
    LFLAG,
    CC,
)
from xonsh.tools import (
    redirect_stdout,
    redirect_stderr,
    print_exception,
    XonshCalledProcessError,
    findfirst,
    on_main_thread,
    XonshError,
    format_std_prepost,
    ALIAS_KWARG_NAMES,
)
from xonsh.lazyasd import lazyobject, LazyObject
from xonsh.jobs import wait_for_active_job, give_terminal_to, _continue
from xonsh.lazyimps import fcntl, termios, _winapi, msvcrt, winutils

# these decorators are imported for users back-compatible
from xonsh.tools import unthreadable, uncapturable  # NOQA

# foreground has be deprecated
foreground = unthreadable


@lazyobject
def STDOUT_CAPTURE_KINDS():
    return frozenset(["stdout", "object"])


# The following escape codes are xterm codes.
# See http://rtfm.etla.org/xterm/ctlseq.html for more.
MODE_NUMS = ("1049", "47", "1047")
START_ALTERNATE_MODE = LazyObject(
    lambda: frozenset("\x1b[?{0}h".format(i).encode() for i in MODE_NUMS),
    globals(),
    "START_ALTERNATE_MODE",
)
END_ALTERNATE_MODE = LazyObject(
    lambda: frozenset("\x1b[?{0}l".format(i).encode() for i in MODE_NUMS),
    globals(),
    "END_ALTERNATE_MODE",
)
ALTERNATE_MODE_FLAGS = LazyObject(
    lambda: tuple(START_ALTERNATE_MODE) + tuple(END_ALTERNATE_MODE),
    globals(),
    "ALTERNATE_MODE_FLAGS",
)
RE_HIDDEN_BYTES = LazyObject(
    lambda: re.compile(b"(\001.*?\002)"), globals(), "RE_HIDDEN"
)


@lazyobject
def RE_VT100_ESCAPE():
    return re.compile(b"(\x9B|\x1B\\[)[0-?]*[ -\\/]*[@-~]")


@lazyobject
def RE_HIDE_ESCAPE():
    return re.compile(
        b"(" + RE_HIDDEN_BYTES.pattern + b"|" + RE_VT100_ESCAPE.pattern + b")"
    )


class QueueReader:
    """Provides a file-like interface to reading from a queue."""

    def __init__(self, fd, timeout=None):
        """
        Parameters
        ----------
        fd : int
            A file descriptor
        timeout : float or None, optional
            The queue reading timeout.
        """
        self.fd = fd
        self.timeout = timeout
        self.closed = False
        self.queue = queue.Queue()
        self.thread = None