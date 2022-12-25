"""Implements a xonsh tracer."""
import os
import re
import sys
import inspect
import argparse
import linecache
import importlib
import functools

from xonsh.lazyasd import LazyObject
from xonsh.platform import HAS_PYGMENTS
from xonsh.tools import DefaultNotGiven, print_color, normabspath, to_bool
from xonsh.inspectors import find_file, getouterframes
from xonsh.lazyimps import pygments, pyghooks
from xonsh.proc import STDOUT_CAPTURE_KINDS
import xonsh.prompt.cwd as prompt

terminal = LazyObject(
    lambda: importlib.import_module("pygments.formatters.terminal"),
    globals(),
    "terminal",
)


class TracerType(object):
    """Represents a xonsh tracer object, which keeps track of all tracing
    state. This is a singleton.
    """

    _inst = None
    valid_events = frozenset(["line", "call"])

    def __new__(cls, *args, **kwargs):
        if cls._inst is None:
            cls._inst = super(TracerType, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        self.prev_tracer = DefaultNotGiven
        self.files = set()
        self.usecolor = True
        self.lexer = pyghooks.XonshLexer()
        self.formatter = terminal.TerminalFormatter()
        self._last = ("", -1)  # filename, lineno tuple

    def __del__(self):
        for f in set(self.files):
            self.stop(f)

    def color_output(self, usecolor):
        """Specify whether or not the tracer output shoul