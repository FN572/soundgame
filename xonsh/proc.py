
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

    def close(self):
        """close the reader"""
        self.closed = True

    def is_fully_read(self):
        """Returns whether or not the queue is fully read and the reader is
        closed.
        """
        return (
            self.closed
            and (self.thread is None or not self.thread.is_alive())
            and self.queue.empty()
        )

    def read_queue(self):
        """Reads a single chunk from the queue. This is blocking if
        the timeout is None and non-blocking otherwise.
        """
        try:
            return self.queue.get(block=True, timeout=self.timeout)
        except queue.Empty:
            return b""

    def read(self, size=-1):
        """Reads bytes from the file."""
        i = 0
        buf = b""
        while size < 0 or i != size:
            line = self.read_queue()
            if line:
                buf += line
            else:
                break
            i += len(line)
        return buf

    def readline(self, size=-1):
        """Reads a line, or a partial line from the file descriptor."""
        i = 0
        nl = b"\n"
        buf = b""
        while size < 0 or i != size:
            line = self.read_queue()
            if line:
                buf += line
                if line.endswith(nl):
                    break
            else:
                break
            i += len(line)
        return buf

    def _read_all_lines(self):
        """This reads all remaining lines in a blocking fashion."""
        lines = []
        while not self.is_fully_read():
            chunk = self.read_queue()
            lines.extend(chunk.splitlines(keepends=True))
        return lines

    def readlines(self, hint=-1):
        """Reads lines from the file descriptor. This is blocking for negative
        hints (i.e. read all the remaining lines) and non-blocking otherwise.
        """
        if hint == -1:
            return self._read_all_lines()
        lines = []
        while len(lines) != hint:
            chunk = self.read_queue()
            if not chunk:
                break
            lines.extend(chunk.splitlines(keepends=True))
        return lines

    def fileno(self):
        """Returns the file descriptor number."""
        return self.fd

    @staticmethod
    def readable():
        """Returns true, because this object is always readable."""
        return True

    def iterqueue(self):
        """Iterates through all remaining chunks in a blocking fashion."""
        while not self.is_fully_read():
            chunk = self.read_queue()
            if not chunk:
                continue
            yield chunk


def populate_fd_queue(reader, fd, queue):
    """Reads 1 kb of data from a file descriptor into a queue.
    If this ends or fails, it flags the calling reader object as closed.
    """
    while True:
        try:
            c = os.read(fd, 1024)
        except OSError:
            reader.closed = True
            break
        if c:
            queue.put(c)
        else:
            reader.closed = True
            break


class NonBlockingFDReader(QueueReader):
    """A class for reading characters from a file descriptor on a background
    thread. This has the advantages that the calling thread can close the
    file and that the reading does not block the calling thread.
    """

    def __init__(self, fd, timeout=None):
        """
        Parameters
        ----------
        fd : int
            A file descriptor
        timeout : float or None, optional
            The queue reading timeout.
        """
        super().__init__(fd, timeout=timeout)
        # start reading from stream
        self.thread = threading.Thread(
            target=populate_fd_queue, args=(self, self.fd, self.queue)
        )
        self.thread.daemon = True
        self.thread.start()


def populate_buffer(reader, fd, buffer, chunksize):
    """Reads bytes from the file descriptor and copies them into a buffer.

    The reads happen in parallel using the pread() syscall; which is only
    available on POSIX systems. If the read fails for any reason, the reader is
    flagged as closed.
    """
    offset = 0
    while True:
        try:
            buf = os.pread(fd, chunksize, offset)
        except OSError:
            reader.closed = True
            break
        if buf:
            buffer.write(buf)
            offset += len(buf)
        else:
            reader.closed = True
            break


class BufferedFDParallelReader:
    """Buffered, parallel background thread reader."""

    def __init__(self, fd, buffer=None, chunksize=1024):
        """
        Parameters
        ----------
        fd : int
            File descriptor from which to read.
        buffer : binary file-like or None, optional
            A buffer to write bytes into. If None, a new BytesIO object
            is created.
        chunksize : int, optional
            The max size of the parallel reads, default 1 kb.
        """
        self.fd = fd
        self.buffer = io.BytesIO() if buffer is None else buffer
        self.chunksize = chunksize
        self.closed = False
        # start reading from stream
        self.thread = threading.Thread(
            target=populate_buffer, args=(self, fd, self.buffer, chunksize)
        )
        self.thread.daemon = True

        self.thread.start()


def _expand_console_buffer(cols, max_offset, expandsize, orig_posize, fd):
    # if we are getting close to the end of the console buffer,
    # expand it so that we can read from it successfully.
    if cols == 0:
        return orig_posize[-1], max_offset, orig_posize
    rows = ((max_offset + expandsize) // cols) + 1
    winutils.set_console_screen_buffer_size(cols, rows, fd=fd)
    orig_posize = orig_posize[:3] + (rows,)
    max_offset = (rows - 1) * cols
    return rows, max_offset, orig_posize


def populate_console(reader, fd, buffer, chunksize, queue, expandsize=None):
    """Reads bytes from the file descriptor and puts lines into the queue.
    The reads happened in parallel,
    using xonsh.winutils.read_console_output_character(),
    and is thus only available on windows. If the read fails for any reason,
    the reader is flagged as closed.
    """
    # OK, so this function is super annoying because Windows stores its
    # buffers as a 2D regular, dense array -- without trailing newlines.
    # Meanwhile, we want to add *lines* to the queue. Also, as is typical
    # with parallel reads, the entire buffer that you ask for may not be
    # filled. Thus we have to deal with the full generality.
    #   1. reads may end in the middle of a line
    #   2. excess whitespace at the end of a line may not be real, unless
    #   3. you haven't read to the end of the line yet!
    # So there are alignment issues everywhere.  Also, Windows will automatically
    # read past the current cursor position, even though there is presumably
    # nothing to see there.
    #
    # These chunked reads basically need to happen like this because,
    #   a. The default buffer size is HUGE for the console (90k lines x 120 cols)
    #      as so we can't just read in everything at the end and see what we
    #      care about without a noticeable performance hit.
    #   b. Even with this huge size, it is still possible to write more lines than
    #      this, so we should scroll along with the console.
    # Unfortunately, because we do not have control over the terminal emulator,
    # It is not possible to compute how far back we should set the beginning
    # read position because we don't know how many characters have been popped
    # off the top of the buffer. If we did somehow know this number we could do
    # something like the following:
    #
    #    new_offset = (y*cols) + x
    #    if new_offset == max_offset:
    #        new_offset -= scrolled_offset
    #        x = new_offset%cols
    #        y = new_offset//cols
    #        continue
    #
    # So this method is imperfect and only works as long as the screen has
    # room to expand to.  Thus the trick here is to expand the screen size
    # when we get close enough to the end of the screen. There remain some
    # async issues related to not being able to set the cursor position.
    # but they just affect the alignment / capture of the output of the
    # first command run after a screen resize.
    if expandsize is None:
        expandsize = 100 * chunksize
    x, y, cols, rows = posize = winutils.get_position_size(fd)
    pre_x = pre_y = -1
    orig_posize = posize
    offset = (cols * y) + x
    max_offset = (rows - 1) * cols
    # I believe that there is a bug in PTK that if we reset the
    # cursor position, the cursor on the next prompt is accidentally on
    # the next line.  If this is fixed, uncomment the following line.
    # if max_offset < offset + expandsize:
    #     rows, max_offset, orig_posize = _expand_console_buffer(
    #                                        cols, max_offset, expandsize,
    #                                        orig_posize, fd)
    #     winutils.set_console_cursor_position(x, y, fd=fd)
    while True:
        posize = winutils.get_position_size(fd)
        offset = (cols * y) + x
        if ((posize[1], posize[0]) <= (y, x) and posize[2:] == (cols, rows)) or (
            pre_x == x and pre_y == y
        ):
            # already at or ahead of the current cursor position.
            if reader.closed:
                break
            else:
                time.sleep(reader.timeout)
                continue
        elif max_offset <= offset + expandsize:
            ecb = _expand_console_buffer(cols, max_offset, expandsize, orig_posize, fd)
            rows, max_offset, orig_posize = ecb
            continue
        elif posize[2:] == (cols, rows):
            # cursor updated but screen size is the same.
            pass
        else:
            # screen size changed, which is offset preserving
            orig_posize = posize
            cols, rows = posize[2:]
            x = offset % cols
            y = offset // cols
            pre_x = pre_y = -1
            max_offset = (rows - 1) * cols
            continue
        try:
            buf = winutils.read_console_output_character(
                x=x, y=y, fd=fd, buf=buffer, bufsize=chunksize, raw=True
            )
        except (OSError, IOError):
            reader.closed = True
            break
        # cursor position and offset
        if not reader.closed:
            buf = buf.rstrip()
        nread = len(buf)
        if nread == 0:
            time.sleep(reader.timeout)
            continue
        cur_x, cur_y = posize[0], posize[1]
        cur_offset = (cols * cur_y) + cur_x
        beg_offset = (cols * y) + x
        end_offset = beg_offset + nread
        if end_offset > cur_offset and cur_offset != max_offset:
            buf = buf[: cur_offset - end_offset]
        # convert to lines
        xshift = cols - x
        yshift = (nread // cols) + (1 if nread % cols > 0 else 0)
        lines = [buf[:xshift]]
        lines += [
            buf[l * cols + xshift : (l + 1) * cols + xshift] for l in range(yshift)
        ]
        lines = [line for line in lines if line]
        if not lines:
            time.sleep(reader.timeout)
            continue
        # put lines in the queue
        nl = b"\n"
        for line in lines[:-1]:
            queue.put(line.rstrip() + nl)
        if len(lines[-1]) == xshift:
            queue.put(lines[-1].rstrip() + nl)
        else:
            queue.put(lines[-1])
        # update x and y locations
        if (beg_offset + len(buf)) % cols == 0:
            new_offset = beg_offset + len(buf)
        else:
            new_offset = beg_offset + len(buf.rstrip())
        pre_x = x
        pre_y = y
        x = new_offset % cols
        y = new_offset // cols
        time.sleep(reader.timeout)


class ConsoleParallelReader(QueueReader):
    """Parallel reader for consoles that runs in a background thread.
    This is only needed, available, and useful on Windows.
    """

    def __init__(self, fd, buffer=None, chunksize=1024, timeout=None):
        """
        Parameters
        ----------
        fd : int
            Standard buffer file descriptor, 0 for stdin, 1 for stdout (default),
            and 2 for stderr.
        buffer : ctypes.c_wchar_p, optional
            An existing buffer to (re-)use.
        chunksize : int, optional
            The max size of the parallel reads, default 1 kb.
        timeout : float, optional
            The queue reading timeout.
        """
        timeout = timeout or builtins.__xonsh__.env.get("XONSH_PROC_FREQUENCY")
        super().__init__(fd, timeout=timeout)
        self._buffer = buffer  # this cannot be public
        if buffer is None:
            self._buffer = ctypes.c_char_p(b" " * chunksize)
        self.chunksize = chunksize
        # start reading from stream
        self.thread = threading.Thread(
            target=populate_console,
            args=(self, fd, self._buffer, chunksize, self.queue),
        )
        self.thread.daemon = True
        self.thread.start()


def safe_fdclose(handle, cache=None):
    """Closes a file handle in the safest way possible, and potentially
    storing the result.
    """
    if cache is not None and cache.get(handle, False):
        return
    status = True
    if handle is None:
        pass
    elif isinstance(handle, int):
        if handle >= 3:
            # don't close stdin, stdout, stderr, -1
            try:
                os.close(handle)
            except OSError:
                status = False
    elif handle is sys.stdin or handle is sys.stdout or handle is sys.stderr:
        # don't close stdin, stdout, or stderr
        pass
    else:
        try:
            handle.close()
        except OSError:
            status = False
    if cache is not None:
        cache[handle] = status


def safe_flush(handle):
    """Attempts to safely flush a file handle, returns success bool."""
    status = True
    try:
        handle.flush()
    except OSError:
        status = False
    return status


def still_writable(fd):
    """Determines whether a file descriptor is still writable by trying to
    write an empty string and seeing if it fails.
    """
    try:
        os.write(fd, b"")
        status = True
    except OSError:
        status = False
    return status


class PopenThread(threading.Thread):
    """A thread for running and managing subprocess. This allows reading
    from the stdin, stdout, and stderr streams in a non-blocking fashion.

    This takes the same arguments and keyword arguments as regular Popen.
    This requires that the captured_stdout and captured_stderr attributes
    to be set following instantiation.
    """

    def __init__(self, *args, stdin=None, stdout=None, stderr=None, **kwargs):
        super().__init__()
        self.lock = threading.RLock()
        env = builtins.__xonsh__.env
        # stdin setup
        self.orig_stdin = stdin
        if stdin is None:
            self.stdin_fd = 0
        elif isinstance(stdin, int):
            self.stdin_fd = stdin
        else:
            self.stdin_fd = stdin.fileno()
        self.store_stdin = env.get("XONSH_STORE_STDIN")
        self.timeout = env.get("XONSH_PROC_FREQUENCY")
        self.in_alt_mode = False
        self.stdin_mode = None
        # stdout setup
        self.orig_stdout = stdout
        self.stdout_fd = 1 if stdout is None else stdout.fileno()
        self._set_pty_size()
        # stderr setup
        self.orig_stderr = stderr
        # Set some signal handles, if we can. Must come before process
        # is started to prevent deadlock on windows
        self.proc = None  # has to be here for closure for handles
        self.old_int_handler = self.old_winch_handler = None
        self.old_tstp_handler = self.old_quit_handler = None
        if on_main_thread():
            self.old_int_handler = signal.signal(signal.SIGINT, self._signal_int)
            if ON_POSIX:
                self.old_tstp_handler = signal.signal(signal.SIGTSTP, self._signal_tstp)
                self.old_quit_handler = signal.signal(signal.SIGQUIT, self._signal_quit)
            if CAN_RESIZE_WINDOW:
                self.old_winch_handler = signal.signal(
                    signal.SIGWINCH, self._signal_winch
                )
        # start up process
        if ON_WINDOWS and stdout is not None:
            os.set_inheritable(stdout.fileno(), False)

        try:
            self.proc = proc = subprocess.Popen(
                *args, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs
            )
        except Exception:
            self._clean_up()
            raise

        self.pid = proc.pid
        self.universal_newlines = uninew = proc.universal_newlines
        if uninew:
            self.encoding = enc = env.get("XONSH_ENCODING")
            self.encoding_errors = err = env.get("XONSH_ENCODING_ERRORS")
            self.stdin = io.BytesIO()  # stdin is always bytes!
            self.stdout = io.TextIOWrapper(io.BytesIO(), encoding=enc, errors=err)
            self.stderr = io.TextIOWrapper(io.BytesIO(), encoding=enc, errors=err)
        else:
            self.encoding = self.encoding_errors = None
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.stderr = io.BytesIO()
        self.suspended = False
        self.prevs_are_closed = False
        self.start()

    def run(self):
        """Runs the subprocess by performing a parallel read on stdin if allowed,
        and copying bytes from captured_stdout to stdout and bytes from
        captured_stderr to stderr.
        """
        proc = self.proc
        spec = self._wait_and_getattr("spec")
        # get stdin and apply parallel reader if needed.
        stdin = self.stdin
        if self.orig_stdin is None:
            origin = None
        elif ON_POSIX and self.store_stdin:
            origin = self.orig_stdin
            origfd = origin if isinstance(origin, int) else origin.fileno()
            origin = BufferedFDParallelReader(origfd, buffer=stdin)
        else:
            origin = None
        # get non-blocking stdout
        stdout = self.stdout.buffer if self.universal_newlines else self.stdout
        capout = spec.captured_stdout
        if capout is None:
            procout = None
        else:
            procout = NonBlockingFDReader(capout.fileno(), timeout=self.timeout)
        # get non-blocking stderr
        stderr = self.stderr.buffer if self.universal_newlines else self.stderr
        caperr = spec.captured_stderr
        if caperr is None:
            procerr = None
        else:
            procerr = NonBlockingFDReader(caperr.fileno(), timeout=self.timeout)
        # initial read from buffer
        self._read_write(procout, stdout, sys.__stdout__)
        self._read_write(procerr, stderr, sys.__stderr__)
        # loop over reads while process is running.
        i = j = cnt = 1
        while proc.poll() is None:
            # this is here for CPU performance reasons.
            if i + j == 0:
                cnt = min(cnt + 1, 1000)
                tout = self.timeout * cnt
                if procout is not None:
                    procout.timeout = tout
                if procerr is not None:
                    procerr.timeout = tout
            elif cnt == 1:
                pass
            else:
                cnt = 1
                if procout is not None:
                    procout.timeout = self.timeout
                if procerr is not None:
                    procerr.timeout = self.timeout
            # redirect some output!
            i = self._read_write(procout, stdout, sys.__stdout__)
            j = self._read_write(procerr, stderr, sys.__stderr__)
            if self.suspended:
                break
        if self.suspended:
            return
        # close files to send EOF to non-blocking reader.
        # capout & caperr seem to be needed only by Windows, while
        # orig_stdout & orig_stderr are need by posix and Windows.
        # Also, order seems to matter here,
        # with orig_* needed to be closed before cap*
        safe_fdclose(self.orig_stdout)
        safe_fdclose(self.orig_stderr)
        if ON_WINDOWS:
            safe_fdclose(capout)
            safe_fdclose(caperr)
        # read in the remaining data in a blocking fashion.
        while (procout is not None and not procout.is_fully_read()) or (
            procerr is not None and not procerr.is_fully_read()
        ):
            self._read_write(procout, stdout, sys.__stdout__)
            self._read_write(procerr, stderr, sys.__stderr__)
        # kill the process if it is still alive. Happens when piping.
        if proc.poll() is None:
            proc.terminate()

    def _wait_and_getattr(self, name):
        """make sure the instance has a certain attr, and return it."""
        while not hasattr(self, name):
            time.sleep(1e-7)
        return getattr(self, name)

    def _read_write(self, reader, writer, stdbuf):
        """Reads a chunk of bytes from a buffer and write into memory or back
        down to the standard buffer, as appropriate. Returns the number of
        successful reads.
        """
        if reader is None:
            return 0
        i = -1
        for i, chunk in enumerate(iter(reader.read_queue, b"")):
            self._alt_mode_switch(chunk, writer, stdbuf)
        if i >= 0:
            writer.flush()
            stdbuf.flush()
        return i + 1

    def _alt_mode_switch(self, chunk, membuf, stdbuf):
        """Enables recursively switching between normal capturing mode
        and 'alt' mode, which passes through values to the standard
        buffer. Pagers, text editors, curses applications, etc. use
        alternate mode.
        """
        i, flag = findfirst(chunk, ALTERNATE_MODE_FLAGS)
        if flag is None:
            self._alt_mode_writer(chunk, membuf, stdbuf)
        else:
            # This code is executed when the child process switches the
            # terminal into or out of alternate mode. The line below assumes
            # that the user has opened vim, less, or similar, and writes writes
            # to stdin.
            j = i + len(flag)
            # write the first part of the chunk in the current mode.
            self._alt_mode_writer(chunk[:i], membuf, stdbuf)
            # switch modes
            # write the flag itself the current mode where alt mode is on
            # so that it is streamed to the terminal ASAP.
            # this is needed for terminal emulators to find the correct
            # positions before and after alt mode.
            alt_mode = flag in START_ALTERNATE_MODE
            if alt_mode:
                self.in_alt_mode = alt_mode
                self._alt_mode_writer(flag, membuf, stdbuf)
                self._enable_cbreak_stdin()
            else:
                self._alt_mode_writer(flag, membuf, stdbuf)
                self.in_alt_mode = alt_mode
                self._disable_cbreak_stdin()
            # recurse this function, but without the current flag.
            self._alt_mode_switch(chunk[j:], membuf, stdbuf)

    def _alt_mode_writer(self, chunk, membuf, stdbuf):
        """Write bytes to the standard buffer if in alt mode or otherwise
        to the in-memory buffer.
        """
        if not chunk:
            pass  # don't write empty values
        elif self.in_alt_mode:
            stdbuf.buffer.write(chunk)
        else:
            with self.lock:
                p = membuf.tell()
                membuf.seek(0, io.SEEK_END)
                membuf.write(chunk)
                membuf.seek(p)

    #
    # Window resize handlers
    #

    def _signal_winch(self, signum, frame):
        """Signal handler for SIGWINCH - window size has changed."""
        self.send_signal(signal.SIGWINCH)
        self._set_pty_size()

    def _set_pty_size(self):
        """Sets the window size of the child pty based on the window size of
        our own controlling terminal.
        """
        if ON_WINDOWS or not os.isatty(self.stdout_fd):
            return
        # Get the terminal size of the real terminal, set it on the
        #       pseudoterminal.
        buf = array.array("h", [0, 0, 0, 0])
        # 1 = stdout here
        try:
            fcntl.ioctl(1, termios.TIOCGWINSZ, buf, True)
            fcntl.ioctl(self.stdout_fd, termios.TIOCSWINSZ, buf)
        except OSError:
            pass

    #
    # SIGINT handler
    #

    def _signal_int(self, signum, frame):
        """Signal handler for SIGINT - Ctrl+C may have been pressed."""
        self.send_signal(signum)
        if self.proc is not None and self.proc.poll() is not None:
            self._restore_sigint(frame=frame)
        if on_main_thread():
            signal.pthread_kill(threading.get_ident(), signal.SIGINT)

    def _restore_sigint(self, frame=None):
        old = self.old_int_handler
        if old is not None:
            if on_main_thread():
                signal.signal(signal.SIGINT, old)
            self.old_int_handler = None
        if frame is not None:
            self._disable_cbreak_stdin()
            if old is not None and old is not self._signal_int:
                old(signal.SIGINT, frame)

    #
    # SIGTSTP handler
    #

    def _signal_tstp(self, signum, frame):
        """Signal handler for suspending SIGTSTP - Ctrl+Z may have been pressed.
        """
        self.suspended = True
        self.send_signal(signum)
        self._restore_sigtstp(frame=frame)

    def _restore_sigtstp(self, frame=None):
        old = self.old_tstp_handler
        if old is not None:
            if on_main_thread():
                signal.signal(signal.SIGTSTP, old)
            self.old_tstp_handler = None
        if frame is not None:
            self._disable_cbreak_stdin()

    #
    # SIGQUIT handler
    #

    def _signal_quit(self, signum, frame):
        r"""Signal handler for quiting SIGQUIT - Ctrl+\ may have been pressed.
        """
        self.send_signal(signum)
        self._restore_sigquit(frame=frame)

    def _restore_sigquit(self, frame=None):
        old = self.old_quit_handler
        if old is not None:
            if on_main_thread():
                signal.signal(signal.SIGQUIT, old)
            self.old_quit_handler = None
        if frame is not None:
            self._disable_cbreak_stdin()

    #
    # cbreak mode handlers
    #

    def _enable_cbreak_stdin(self):
        if not ON_POSIX:
            return
        try:
            self.stdin_mode = termios.tcgetattr(self.stdin_fd)[:]
        except termios.error:
            # this can happen for cases where another process is controlling
            # xonsh's tty device, such as in testing.
            self.stdin_mode = None
            return
        new = self.stdin_mode[:]
        new[LFLAG] &= ~(termios.ECHO | termios.ICANON)
        new[CC][termios.VMIN] = 1
        new[CC][termios.VTIME] = 0
        try:
            # termios.TCSAFLUSH may be less reliable than termios.TCSANOW
            termios.tcsetattr(self.stdin_fd, termios.TCSANOW, new)
        except termios.error:
            self._disable_cbreak_stdin()

    def _disable_cbreak_stdin(self):
        if not ON_POSIX or self.stdin_mode is None:
            return
        new = self.stdin_mode[:]
        new[LFLAG] |= termios.ECHO | termios.ICANON
        new[CC][termios.VMIN] = 1
        new[CC][termios.VTIME] = 0
        try:
            termios.tcsetattr(self.stdin_fd, termios.TCSANOW, new)
        except termios.error:
            pass

    #
    # Dispatch methods
    #

    def poll(self):
        """Dispatches to Popen.returncode."""
        return self.proc.returncode

    def wait(self, timeout=None):
        """Dispatches to Popen.wait(), but also does process cleanup such as
        joining this thread and replacing the original window size signal
        handler.
        """
        self._disable_cbreak_stdin()
        rtn = self.proc.wait(timeout=timeout)
        self.join()
        # need to replace the old signal handlers somewhere...
        if self.old_winch_handler is not None and on_main_thread():
            signal.signal(signal.SIGWINCH, self.old_winch_handler)
            self.old_winch_handler = None
        self._clean_up()
        return rtn

    def _clean_up(self):
        self._restore_sigint()
        self._restore_sigtstp()
        self._restore_sigquit()

    @property
    def returncode(self):
        """Process return code."""
        return self.proc.returncode

    @returncode.setter
    def returncode(self, value):
        """Process return code."""
        self.proc.returncode = value

    @property
    def signal(self):
        """Process signal, or None."""
        s = getattr(self.proc, "signal", None)
        if s is None:
            rtn = self.returncode
            if rtn is not None and rtn != 0:
                s = (-1 * rtn, rtn < 0 if ON_WINDOWS else os.WCOREDUMP(rtn))
        return s

    @signal.setter
    def signal(self, value):
        """Process signal, or None."""
        self.proc.signal = value

    def send_signal(self, signal):
        """Dispatches to Popen.send_signal()."""
        dt = 0.0
        while self.proc is None and dt < self.timeout:
            time.sleep(1e-7)
            dt += 1e-7
        if self.proc is None:
            return
        try:
            rtn = self.proc.send_signal(signal)
        except ProcessLookupError:
            # This can happen in the case of !(cmd) when the command has ended
            rtn = None
        return rtn

    def terminate(self):
        """Dispatches to Popen.terminate()."""
        return self.proc.terminate()

    def kill(self):
        """Dispatches to Popen.kill()."""
        return self.proc.kill()


class Handle(int):
    closed = False

    def Close(self, CloseHandle=None):
        CloseHandle = CloseHandle or _winapi.CloseHandle
        if not self.closed:
            self.closed = True
            CloseHandle(self)

    def Detach(self):
        if not self.closed:
            self.closed = True
            return int(self)
        raise ValueError("already closed")

    def __repr__(self):
        return "Handle(%d)" % int(self)

    __del__ = Close
    __str__ = __repr__


class FileThreadDispatcher:
    """Dispatches to different file handles depending on the
    current thread. Useful if you want file operation to go to different
    places for different threads.
    """

    def __init__(self, default=None):
        """
        Parameters
        ----------
        default : file-like or None, optional
            The file handle to write to if a thread cannot be found in
            the registry. If None, a new in-memory instance.

        Attributes
        ----------
        registry : dict
            Maps thread idents to file handles.
        """
        if default is None:
            default = io.TextIOWrapper(io.BytesIO())
        self.default = default
        self.registry = {}

    def register(self, handle):
        """Registers a file handle for the current thread. Returns self so
        that this method can be used in a with-statement.
        """
        if handle is self:
            # prevent weird recurssion errors
            return self
        self.registry[threading.get_ident()] = handle
        return self

    def deregister(self):
        """Removes the current thread from the registry."""
        ident = threading.get_ident()
        if ident in self.registry:
            # don't remove if we have already been deregistered
            del self.registry[threading.get_ident()]

    @property
    def available(self):
        """True if the thread is available in the registry."""
        return threading.get_ident() in self.registry

    @property
    def handle(self):
        """Gets the current handle for the thread."""
        return self.registry.get(threading.get_ident(), self.default)

    def __enter__(self):
        pass

    def __exit__(self, ex_type, ex_value, ex_traceback):
        self.deregister()

    #
    # io.TextIOBase interface
    #

    @property
    def encoding(self):
        """Gets the encoding for this thread's handle."""
        return self.handle.encoding

    @property
    def errors(self):
        """Gets the errors for this thread's handle."""
        return self.handle.errors

    @property
    def newlines(self):
        """Gets the newlines for this thread's handle."""
        return self.handle.newlines

    @property
    def buffer(self):
        """Gets the buffer for this thread's handle."""
        return self.handle.buffer

    def detach(self):
        """Detaches the buffer for the current thread."""
        return self.handle.detach()

    def read(self, size=None):
        """Reads from the handle for the current thread."""
        return self.handle.read(size)

    def readline(self, size=-1):
        """Reads a line from the handle for the current thread."""
        return self.handle.readline(size)

    def readlines(self, hint=-1):
        """Reads lines from the handle for the current thread."""
        return self.handle.readlines(hint)

    def seek(self, offset, whence=io.SEEK_SET):
        """Seeks the current file."""
        return self.handle.seek(offset, whence)

    def tell(self):
        """Reports the current position in the handle for the current thread."""
        return self.handle.tell()

    def write(self, s):
        """Writes to this thread's handle. This also flushes, just to be
        extra sure the string was written.
        """
        h = self.handle
        try:
            r = h.write(s)
            h.flush()
        except OSError:
            r = None
        return r

    @property
    def line_buffering(self):
        """Gets if line buffering for this thread's handle enabled."""
        return self.handle.line_buffering

    #
    # io.IOBase interface
    #

    def close(self):
        """Closes the current thread's handle."""
        return self.handle.close()

    @property
    def closed(self):
        """Is the thread's handle closed."""
        return self.handle.closed

    def fileno(self):
        """Returns the file descriptor for the current thread."""
        return self.handle.fileno()

    def flush(self):
        """Flushes the file descriptor for the current thread."""
        return safe_flush(self.handle)

    def isatty(self):
        """Returns if the file descriptor for the current thread is a tty."""
        return self.handle.isatty()

    def readable(self):
        """Returns if file descriptor for the current thread is readable."""
        return self.handle.readable()

    def seekable(self):
        """Returns if file descriptor for the current thread is seekable."""
        return self.handle.seekable()

    def truncate(self, size=None):
        """Truncates the file for for the current thread."""
        return self.handle.truncate()

    def writable(self, size=None):
        """Returns if file descriptor for the current thread is writable."""
        return self.handle.writable(size)

    def writelines(self):
        """Writes lines for the file descriptor for the current thread."""
        return self.handle.writelines()


# These should NOT be lazy since they *need* to get the true stdout from the
# main thread. Also their creation time should be negligible.
STDOUT_DISPATCHER = FileThreadDispatcher(default=sys.stdout)
STDERR_DISPATCHER = FileThreadDispatcher(default=sys.stderr)


def parse_proxy_return(r, stdout, stderr):
    """Proxies may return a variety of outputs. This handles them generally.

    Parameters
    ----------
    r : tuple, str, int, or None
        Return from proxy function
    stdout : file-like
        Current stdout stream
    stdout : file-like
        Current stderr stream

    Returns
    -------
    cmd_result : int
        The return code of the proxy
    """
    cmd_result = 0
    if isinstance(r, str):
        stdout.write(r)
        stdout.flush()
    elif isinstance(r, int):
        cmd_result = r
    elif isinstance(r, cabc.Sequence):
        rlen = len(r)
        if rlen > 0 and r[0] is not None:
            stdout.write(r[0])
            stdout.flush()
        if rlen > 1 and r[1] is not None:
            stderr.write(r[1])
            stderr.flush()
        if rlen > 2 and r[2] is not None:
            cmd_result = r[2]
    elif r is not None:
        # for the random object...
        stdout.write(str(r))
        stdout.flush()
    return cmd_result


def proxy_zero(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes no parameters."""
    return f()


def proxy_one(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes one parameter: args"""
    return f(args)


def proxy_two(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes two parameter: args and stdin."""
    return f(args, stdin)


def proxy_three(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes three parameter: args, stdin, stdout.
    """
    return f(args, stdin, stdout)


def proxy_four(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes four parameter: args, stdin, stdout,
    and stderr.
    """
    return f(args, stdin, stdout, stderr)


def proxy_five(f, args, stdin, stdout, stderr, spec, stack):
    """Calls a proxy function which takes four parameter: args, stdin, stdout,
    stderr, and spec.
    """
    return f(args, stdin, stdout, stderr, spec)


PROXIES = (proxy_zero, proxy_one, proxy_two, proxy_three, proxy_four, proxy_five)


def partial_proxy(f):
    """Dispatches the appropriate proxy function based on the number of args."""
    numargs = 0
    for name, param in inspect.signature(f).parameters.items():
        if (
            param.kind == param.POSITIONAL_ONLY
            or param.kind == param.POSITIONAL_OR_KEYWORD
        ):
            numargs += 1
        elif name in ALIAS_KWARG_NAMES and param.kind == param.KEYWORD_ONLY:
            numargs += 1
    if numargs < 6:
        return functools.partial(PROXIES[numargs], f)
    elif numargs == 6:
        # don't need to partial.
        return f
    else:
        e = "Expected proxy with 6 or fewer arguments for {}, not {}"
        raise XonshError(e.format(", ".join(ALIAS_KWARG_NAMES), numargs))


class ProcProxyThread(threading.Thread):
    """
    Class representing a function to be run as a subprocess-mode command.
    """

    def __init__(
        self,
        f,
        args,
        stdin=None,
        stdout=None,
        stderr=None,
        universal_newlines=False,
        close_fds=False,
        env=None,
    ):
        """Parameters
        ----------
        f : function
            The function to be executed.
        args : list
            A (possibly empty) list containing the arguments that were given on
            the command line
        stdin : file-like, optional
            A file-like object representing stdin (input can be read from
            here).  If `stdin` is not provided or if it is explicitly set to
            `None`, then an instance of `io.StringIO` representing an empty
            file is used.
        stdout : file-like, optional
            A file-like object representing stdout (normal output can be
            written here).  If `stdout` is not provided or if it is explicitly
            set to `None`, then `sys.stdout` is used.
        stderr : file-like, optional
            A file-like object representing stderr (error output can be
            written here).  If `stderr` is not provided or if it is explicitly
            set to `None`, then `sys.stderr` is used.
        universal_newlines : bool, optional
            Whether or not to use universal newlines.
        close_fds : bool, optional
            Whether or not to close file descriptors. This is here for Popen
            compatability and currently does nothing.
        env : Mapping, optional
            Environment mapping.
        """
        self.orig_f = f
        self.f = partial_proxy(f)
        self.args = args
        self.pid = None
        self.returncode = None
        self._closed_handle_cache = {}

        handles = self._get_handles(stdin, stdout, stderr)
        (
            self.p2cread,
            self.p2cwrite,
            self.c2pread,
            self.c2pwrite,
            self.errread,
            self.errwrite,
        ) = handles

        # default values
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.close_fds = close_fds
        self.env = env or builtins.__xonsh__.env
        self._interrupted = False

        if ON_WINDOWS:
            if self.p2cwrite != -1:
                self.p2cwrite = msvcrt.open_osfhandle(self.p2cwrite.Detach(), 0)
            if self.c2pread != -1:
                self.c2pread = msvcrt.open_osfhandle(self.c2pread.Detach(), 0)
            if self.errread != -1:
                self.errread = msvcrt.open_osfhandle(self.errread.Detach(), 0)
