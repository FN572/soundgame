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
        """Specify whether or not the tracer output should be colored."""
        # we have to use a function to set usecolor because of the way that
        # lazyasd works. Namely, it cannot dispatch setattr to the target
        # object without being unable to access its own __dict__. This makes
        # setting an attr look like getting a function.
        self.usecolor = usecolor

    def start(self, filename):
        """Starts tracing a file."""
        files = self.files
        if len(files) == 0:
            self.prev_tracer = sys.gettrace()
        files.add(normabspath(filename))
        sys.settrace(self.trace)
        curr = inspect.currentframe()
        for frame, fname, *_ in getouterframes(curr, context=0):
            if normabspath(fname) in files:
                frame.f_trace = self.trace

    def stop(self, filename):
        """Stops tracing a file."""
        filename = normabspath(filename)
        self.files.discard(filename)
        if len(self.files) == 0:
            sys.settrace(self.prev_tracer)
            curr = inspect.currentframe()
            for frame, fname, *_ in getouterframes(curr, context=0):
                if normabspath(fname) == filename:
                    frame.f_trace = self.prev_tracer
            self.prev_tracer = DefaultNotGiven

    def trace(self, frame, event, arg):
        """Implements a line tracing function."""
        if event not in self.valid_events:
            return self.trace
        fname = find_file(frame)
        if fname in self.files:
            lineno = frame.f_lineno
            curr = (fname, lineno)
            if curr != self._last:
                line = linecache.getline(fname, lineno).rstrip()
                s = tracer_format_line(
                    fname,
                    lineno,
                    line,
                    color=self.usecolor,
                    lexer=self.lexer,
                    formatter=self.formatter,
                )
                print_color(s)
                self._last = curr
        return self.trace


tracer = LazyObject(TracerType, globals(), "tracer")

COLORLESS_LINE = "{fname}:{lineno}:{line}"
COLOR_LINE = "{{PURPLE}}{fname}{{BLUE}}:" "{{GREEN}}{lineno}{{BLUE}}:" "{{NO_COLOR}}"


def tracer_format_line(fname, lineno, line, color=True, lexer=None, formatter=None):
   