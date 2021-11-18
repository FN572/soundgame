
# -*- coding: utf-8 -*-
"""The base class for xonsh shell"""
import io
import os
import sys
import time
import builtins

from xonsh.tools import (
    XonshError,
    print_exception,
    DefaultNotGiven,
    check_for_partial_string,
    format_std_prepost,
    get_line_continuation,
)
from xonsh.platform import HAS_PYGMENTS, ON_WINDOWS
from xonsh.codecache import (
    should_use_cache,
    code_cache_name,
    code_cache_check,
    get_cache_filename,
    update_cache,
    run_compiled_code,
)
from xonsh.completer import Completer
from xonsh.prompt.base import multiline_prompt, PromptFormatter
from xonsh.events import events
from xonsh.shell import transform_command
from xonsh.lazyimps import pygments, pyghooks
from xonsh.ansi_colors import ansi_partial_color_format

if ON_WINDOWS:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleTitleW.argtypes = [ctypes.c_wchar_p]


class _TeeStdBuf(io.RawIOBase):
    """A dispatcher for bytes to two buffers, as std stream buffer and an
    in memory buffer.
    """

    def __init__(
        self, stdbuf, membuf, encoding=None, errors=None, prestd=b"", poststd=b""
    ):
        """
        Parameters
        ----------
        stdbuf : BytesIO-like or StringIO-like
            The std stream buffer.
        membuf : BytesIO-like
            The in memory stream buffer.
        encoding : str or None, optional
            The encoding of the stream. Only used if stdbuf is a text stream,
            rather than a binary one. Defaults to $XONSH_ENCODING if None.
        errors : str or None, optional
            The error form for the encoding of the stream. Only used if stdbuf
            is a text stream, rather than a binary one. Deafults to
            $XONSH_ENCODING_ERRORS if None.
        prestd : bytes, optional
            The prefix to prepend to the standard buffer.
        poststd : bytes, optional
            The postfix to append to the standard buffer.
        """
        self.stdbuf = stdbuf
        self.membuf = membuf
        env = builtins.__xonsh__.env
        self.encoding = env.get("XONSH_ENCODING") if encoding is None else encoding
        self.errors = env.get("XONSH_ENCODING_ERRORS") if errors is None else errors
        self.prestd = prestd
        self.poststd = poststd
        self._std_is_binary = not hasattr(stdbuf, "encoding")

    def fileno(self):
        """Returns the file descriptor of the std buffer."""
        return self.stdbuf.fileno()

    def seek(self, offset, whence=io.SEEK_SET):
        """Sets the location in both the stdbuf and the membuf."""
        self.stdbuf.seek(offset, whence)
        self.membuf.seek(offset, whence)

    def truncate(self, size=None):
        """Truncate both buffers."""
        self.stdbuf.truncate(size)
        self.membuf.truncate(size)

    def readinto(self, b):
        """Read bytes into buffer from both streams."""
        if self._std_is_binary:
            self.stdbuf.readinto(b)
        return self.membuf.readinto(b)

    def write(self, b):
        """Write bytes into both buffers."""
        std_b = b
        if self.prestd:
            std_b = self.prestd + b
        if self.poststd:
            std_b += self.poststd
        # write to stdbuf
        if self._std_is_binary:
            self.stdbuf.write(std_b)
        else:
            self.stdbuf.write(std_b.decode(encoding=self.encoding, errors=self.errors))
        return self.membuf.write(b)


class _TeeStd(io.TextIOBase):
    """Tees a std stream into an in-memory container and the original stream."""

    def __init__(self, name, mem, prestd="", poststd=""):
        """
        Parameters
        ----------
        name : str
            The name of the buffer in the sys module, e.g. 'stdout'.
        mem : io.TextIOBase-like
            The in-memory text-based representation.
        prestd : str, optional
            The prefix to prepend to the standard stream.
        poststd : str, optional
            The postfix to append to the standard stream.
        """
        self._name = name
        self.std = std = getattr(sys, name)
        self.mem = mem
        self.prestd = prestd
        self.poststd = poststd
        preb = prestd.encode(encoding=mem.encoding, errors=mem.errors)
        postb = poststd.encode(encoding=mem.encoding, errors=mem.errors)
        if hasattr(std, "buffer"):
            buffer = _TeeStdBuf(std.buffer, mem.buffer, prestd=preb, poststd=postb)
        else:
            # TextIO does not have buffer as part of the API, so std streams
            # may not either.
            buffer = _TeeStdBuf(
                std,
                mem.buffer,
                encoding=mem.encoding,
                errors=mem.errors,
                prestd=preb,
                poststd=postb,
            )
        self.buffer = buffer
        setattr(sys, name, self)

    @property
    def encoding(self):
        """The encoding of the in-memory buffer."""
        return self.mem.encoding

    @property
    def errors(self):
        """The errors of the in-memory buffer."""
        return self.mem.errors

    @property
    def newlines(self):
        """The newlines of the in-memory buffer."""
        return self.mem.newlines

    def _replace_std(self):
        std = self.std
        if std is None:
            return
        setattr(sys, self._name, std)
        self.std = self._name = None

    def __del__(self):
        self._replace_std()

    def close(self):
        """Restores the original std stream."""
        self._replace_std()

    def write(self, s):
        """Writes data to the original std stream and the in-memory object."""
        self.mem.write(s)
        if self.std is None:
            return
        std_s = s
        if self.prestd:
            std_s = self.prestd + std_s
        if self.poststd:
            std_s += self.poststd
        self.std.write(std_s)

    def flush(self):
        """Flushes both the original stdout and the buffer."""
        self.std.flush()
        self.mem.flush()

    def fileno(self):
        """Tunnel fileno() calls to the std stream."""
        return self.std.fileno()

    def seek(self, offset, whence=io.SEEK_SET):
        """Seek to a location in both streams."""
        self.std.seek(offset, whence)
        self.mem.seek(offset, whence)

    def truncate(self, size=None):
        """Seek to a location in both streams."""
        self.std.truncate(size)
        self.mem.truncate(size)

    def detach(self):
        """This operation is not supported."""
        raise io.UnsupportedOperation

    def read(self, size=None):
        """Read from the in-memory stream and seek to a new location in the
        std stream.
        """
        s = self.mem.read(size)
        loc = self.std.tell()
        self.std.seek(loc + len(s))
        return s

    def readline(self, size=-1):
        """Read a line from the in-memory stream and seek to a new location
        in the std stream.
        """
        s = self.mem.readline(size)
        loc = self.std.tell()
        self.std.seek(loc + len(s))
        return s


class Tee:
    """Class that merges tee'd stdout and stderr into a single stream.

    This represents what a user would actually see on the command line.
    This class has the same interface as io.TextIOWrapper, except that
    the buffer is optional.
    """

    # pylint is a stupid about counting public methods when using inheritance.
    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        buffer=None,
        encoding=None,
        errors=None,
        newline=None,
        line_buffering=False,
        write_through=False,
    ):
        self.buffer = io.BytesIO() if buffer is None else buffer
        self.memory = io.TextIOWrapper(
            self.buffer,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
            write_through=write_through,
        )
        self.stdout = _TeeStd("stdout", self.memory)
        env = builtins.__xonsh__.env
        prestderr = format_std_prepost(env.get("XONSH_STDERR_PREFIX"))
        poststderr = format_std_prepost(env.get("XONSH_STDERR_POSTFIX"))
        self.stderr = _TeeStd(
            "stderr", self.memory, prestd=prestderr, poststd=poststderr
        )

    @property
    def line_buffering(self):
        return self.memory.line_buffering

    def __del__(self):
        del self.stdout, self.stderr
        self.stdout = self.stderr = None

    def close(self):
        """Closes the buffer as well as the stdout and stderr tees."""
        self.stdout.close()
        self.stderr.close()
        self.memory.close()

    def getvalue(self):
        """Gets the current contents of the in-memory buffer."""
        m = self.memory
        loc = m.tell()
        m.seek(0)
        s = m.read()
        m.seek(loc)
        return s

