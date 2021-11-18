
# -*- coding: utf-8 -*-
"""The xonsh built-ins.

Note that this module is named 'built_ins' so as not to be confused with the
special Python builtins module.
"""
import io
import os
import re
import sys
import types
import shlex
import signal
import atexit
import pathlib
import inspect
import warnings
import builtins
import itertools
import subprocess
import contextlib
import collections.abc as cabc

from xonsh.ast import AST
from xonsh.lazyasd import LazyObject, lazyobject
from xonsh.inspectors import Inspector
from xonsh.aliases import Aliases, make_default_aliases
from xonsh.environ import Env, default_env, locate_binary
from xonsh.jobs import add_job
from xonsh.platform import ON_POSIX, ON_WINDOWS, ON_WSL
from xonsh.proc import (
    PopenThread,
    ProcProxyThread,
    ProcProxy,
    ConsoleParallelReader,
    pause_call_resume,
    CommandPipeline,
    HiddenCommandPipeline,
    STDOUT_CAPTURE_KINDS,
)
from xonsh.tools import (
    suggest_commands,
    expand_path,
    globpath,
    XonshError,
    XonshCalledProcessError,
)
from xonsh.lazyimps import pty, termios
from xonsh.commands_cache import CommandsCache
from xonsh.events import events

import xonsh.completers.init

BUILTINS_LOADED = False
INSPECTOR = LazyObject(Inspector, globals(), "INSPECTOR")

warnings.filterwarnings("once", category=DeprecationWarning)


@lazyobject
def AT_EXIT_SIGNALS():
    sigs = (
        signal.SIGABRT,
        signal.SIGFPE,
        signal.SIGILL,
        signal.SIGSEGV,
        signal.SIGTERM,
    )
    if ON_POSIX:
        sigs += (signal.SIGTSTP, signal.SIGQUIT, signal.SIGHUP)
    return sigs


def resetting_signal_handle(sig, f):
    """Sets a new signal handle that will automatically restore the old value
    once the new handle is finished.
    """
    oldh = signal.getsignal(sig)

    def newh(s=None, frame=None):
        f(s, frame)
        signal.signal(sig, oldh)
        if sig != 0:
            sys.exit(sig)

    signal.signal(sig, newh)


def helper(x, name=""):
    """Prints help about, and then returns that variable."""
    INSPECTOR.pinfo(x, oname=name, detail_level=0)
    return x


def superhelper(x, name=""):
    """Prints help about, and then returns that variable."""
    INSPECTOR.pinfo(x, oname=name, detail_level=1)
    return x


def reglob(path, parts=None, i=None):
    """Regular expression-based globbing."""
    if parts is None:
        path = os.path.normpath(path)
        drive, tail = os.path.splitdrive(path)
        parts = tail.split(os.sep)
        d = os.sep if os.path.isabs(path) else "."
        d = os.path.join(drive, d)
        return reglob(d, parts, i=0)
    base = subdir = path
    if i == 0:
        if not os.path.isabs(base):
            base = ""
        elif len(parts) > 1:
            i += 1
    regex = os.path.join(base, parts[i])
    if ON_WINDOWS:
        # currently unable to access regex backslash sequences
        # on Windows due to paths using \.
        regex = regex.replace("\\", "\\\\")
    regex = re.compile(regex)
    files = os.listdir(subdir)
    files.sort()
    paths = []
    i1 = i + 1
    if i1 == len(parts):
        for f in files:
            p = os.path.join(base, f)
            if regex.fullmatch(p) is not None:
                paths.append(p)
    else:
        for f in files:
            p = os.path.join(base, f)
            if regex.fullmatch(p) is None or not os.path.isdir(p):
                continue
            paths += reglob(p, parts=parts, i=i1)
    return paths


def path_literal(s):
    s = expand_path(s)
    return pathlib.Path(s)


def regexsearch(s):
    s = expand_path(s)
    return reglob(s)


def globsearch(s):
    csc = builtins.__xonsh__.env.get("CASE_SENSITIVE_COMPLETIONS")
    glob_sorted = builtins.__xonsh__.env.get("GLOB_SORTED")
    dotglob = builtins.__xonsh__.env.get("DOTGLOB")
    return globpath(
        s,
        ignore_case=(not csc),
        return_empty=True,
        sort_result=glob_sorted,
        include_dotfiles=dotglob,
    )


def pathsearch(func, s, pymode=False, pathobj=False):
    """
    Takes a string and returns a list of file paths that match (regex, glob,
    or arbitrary search function). If pathobj=True, the return is a list of
    pathlib.Path objects instead of strings.
    """
    if not callable(func) or len(inspect.signature(func).parameters) != 1:
        error = "%r is not a known path search function"
        raise XonshError(error % func)
    o = func(s)
    if pathobj and pymode:
        o = list(map(pathlib.Path, o))
    no_match = [] if pymode else [s]
    return o if len(o) != 0 else no_match


RE_SHEBANG = LazyObject(lambda: re.compile(r"#![ \t]*(.+?)$"), globals(), "RE_SHEBANG")


def _is_binary(fname, limit=80):
    with open(fname, "rb") as f:
        for i in range(limit):
            char = f.read(1)
            if char == b"\0":
                return True
            if char == b"\n":
                return False
            if char == b"":
                return False
    return False


def _un_shebang(x):
    if x == "/usr/bin/env":
        return []
    elif any(x.startswith(i) for i in ["/usr/bin", "/usr/local/bin", "/bin"]):
        x = os.path.basename(x)
    elif x.endswith("python") or x.endswith("python.exe"):
        x = "python"
    if x == "xonsh":
        return ["python", "-m", "xonsh.main"]
    return [x]


def get_script_subproc_command(fname, args):
    """Given the name of a script outside the path, returns a list representing
    an appropriate subprocess command to execute the script.  Raises
    PermissionError if the script is not executable.
    """
    # make sure file is executable
    if not os.access(fname, os.X_OK):
        raise PermissionError
    if ON_POSIX and not os.access(fname, os.R_OK):
        # on some systems, some important programs (e.g. sudo) will have
        # execute permissions but not read/write permissions. This enables
        # things with the SUID set to be run. Needs to come before _is_binary()
        # is called, because that function tries to read the file.
        return [fname] + args
    elif _is_binary(fname):
        # if the file is a binary, we should call it directly
        return [fname] + args
    if ON_WINDOWS:
        # Windows can execute various filetypes directly
        # as given in PATHEXT
        _, ext = os.path.splitext(fname)
        if ext.upper() in builtins.__xonsh__.env.get("PATHEXT"):
            return [fname] + args
    # find interpreter
    with open(fname, "rb") as f:
        first_line = f.readline().decode().strip()
    m = RE_SHEBANG.match(first_line)
    # xonsh is the default interpreter
    if m is None:
        interp = ["xonsh"]
    else:
        interp = m.group(1).strip()
        if len(interp) > 0:
            interp = shlex.split(interp)
        else:
            interp = ["xonsh"]
    if ON_WINDOWS:
        o = []
        for i in interp:
            o.extend(_un_shebang(i))
        interp = o
    return interp + [fname] + args


@lazyobject
def _REDIR_REGEX():
    name = r"(o(?:ut)?|e(?:rr)?|a(?:ll)?|&?\d?)"
    return re.compile("{r}(>?>|<){r}$".format(r=name))


_MODES = LazyObject(lambda: {">>": "a", ">": "w", "<": "r"}, globals(), "_MODES")
_WRITE_MODES = LazyObject(lambda: frozenset({"w", "a"}), globals(), "_WRITE_MODES")
_REDIR_ALL = LazyObject(lambda: frozenset({"&", "a", "all"}), globals(), "_REDIR_ALL")
_REDIR_ERR = LazyObject(lambda: frozenset({"2", "e", "err"}), globals(), "_REDIR_ERR")
_REDIR_OUT = LazyObject(
    lambda: frozenset({"", "1", "o", "out"}), globals(), "_REDIR_OUT"
)
_E2O_MAP = LazyObject(
    lambda: frozenset(
        {"{}>{}".format(e, o) for e in _REDIR_ERR for o in _REDIR_OUT if o != ""}
    ),
    globals(),
    "_E2O_MAP",
)
_O2E_MAP = LazyObject(
    lambda: frozenset(
        {"{}>{}".format(o, e) for e in _REDIR_ERR for o in _REDIR_OUT if o != ""}
    ),
    globals(),
    "_O2E_MAP",
)


def _is_redirect(x):
    return isinstance(x, str) and _REDIR_REGEX.match(x)


def safe_open(fname, mode, buffering=-1):
    """Safely attempts to open a file in for xonsh subprocs."""
    # file descriptors
    try:
        return io.open(fname, mode, buffering=buffering)
    except PermissionError:
        raise XonshError("xonsh: {0}: permission denied".format(fname))
    except FileNotFoundError:
        raise XonshError("xonsh: {0}: no such file or directory".format(fname))
    except Exception:
        raise XonshError("xonsh: {0}: unable to open file".format(fname))


def safe_close(x):
    """Safely attempts to close an object."""
    if not isinstance(x, io.IOBase):
        return
    if x.closed:
        return
    try:
        x.close()
    except Exception:
        pass


def _parse_redirects(r, loc=None):
    """returns origin, mode, destination tuple"""
    orig, mode, dest = _REDIR_REGEX.match(r).groups()
    # redirect to fd
    if dest.startswith("&"):
        try:
            dest = int(dest[1:])
            if loc is None:
                loc, dest = dest, ""  # NOQA
            else:
                e = "Unrecognized redirection command: {}".format(r)
                raise XonshError(e)
        except (ValueError, XonshError):
            raise
        except Exception:
            pass
    mode = _MODES.get(mode, None)
    if mode == "r" and (len(orig) > 0 or len(dest) > 0):
        raise XonshError("Unrecognized redirection command: {}".format(r))
    elif mode in _WRITE_MODES and len(dest) > 0:
        raise XonshError("Unrecognized redirection command: {}".format(r))
    return orig, mode, dest


def _redirect_streams(r, loc=None):
    """Returns stdin, stdout, stderr tuple of redirections."""
    stdin = stdout = stderr = None
    no_ampersand = r.replace("&", "")
    # special case of redirecting stderr to stdout
    if no_ampersand in _E2O_MAP:
        stderr = subprocess.STDOUT
        return stdin, stdout, stderr
    elif no_ampersand in _O2E_MAP:
        stdout = 2  # using 2 as a flag, rather than using a file object
        return stdin, stdout, stderr
    # get streams
    orig, mode, dest = _parse_redirects(r)
    if mode == "r":
        stdin = safe_open(loc, mode)
    elif mode in _WRITE_MODES:
        if orig in _REDIR_ALL:
            stdout = stderr = safe_open(loc, mode)
        elif orig in _REDIR_OUT:
            stdout = safe_open(loc, mode)
        elif orig in _REDIR_ERR:
            stderr = safe_open(loc, mode)
        else:
            raise XonshError("Unrecognized redirection command: {}".format(r))
    else:
        raise XonshError("Unrecognized redirection command: {}".format(r))
    return stdin, stdout, stderr


def default_signal_pauser(n, f):
    """Pauses a signal, as needed."""
    signal.pause()


def no_pg_xonsh_preexec_fn():
    """Default subprocess preexec function for when there is no existing
    pipeline group.
    """
    os.setpgrp()
    signal.signal(signal.SIGTSTP, default_signal_pauser)


class SubprocSpec:
    """A container for specifying how a subprocess command should be
    executed.
    """

    kwnames = ("stdin", "stdout", "stderr", "universal_newlines", "close_fds")

    def __init__(
        self,
        cmd,
        cls=subprocess.Popen,
        stdin=None,
        stdout=None,
        stderr=None,
        universal_newlines=False,
        close_fds=False,
        captured=False,
    ):
        """
        Parameters
        ----------
        cmd : list of str
            Command to be run.
        cls : Popen-like
            Class to run the subprocess with.
        stdin : file-like
            Popen file descriptor or flag for stdin.
        stdout : file-like
            Popen file descriptor or flag for stdout.
        stderr : file-like
            Popen file descriptor or flag for stderr.
        universal_newlines : bool
            Whether or not to use universal newlines.
        close_fds : bool
            Whether or not to close the file descriptiors when the
            process exits.
        captured : bool or str, optional
            The flag for if the subprocess is captured, may be one of:
            False for $[], 'stdout' for $(), 'hiddenobject' for ![], or
            'object' for !().

        Attributes
        ----------
        args : list of str
            Arguments as originally supplied.
        alias : list of str, callable, or None
            The alias that was resolved for this command, if any.
        binary_loc : str or None
            Path to binary to execute.
        is_proxy : bool
            Whether or not the subprocess is or should be run as a proxy.
        background : bool
            Whether or not the subprocess should be started in the background.
        threadable : bool
            Whether or not the subprocess is able to be run in a background
            thread, rather than the main thread.
        pipeline_index : int or None
            The index number of this sepc into the pipeline that is being setup.
        last_in_pipeline : bool
            Whether the subprocess is the last in the execution pipeline.
        captured_stdout : file-like
            Handle to captured stdin
        captured_stderr : file-like
            Handle to captured stderr
        stack : list of FrameInfo namedtuples or None
            The stack of the call-site of alias, if the alias requires it.
            None otherwise.
        """
        self._stdin = self._stdout = self._stderr = None
        # args
        self.cmd = list(cmd)
        self.cls = cls
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.universal_newlines = universal_newlines
        self.close_fds = close_fds
        self.captured = captured
        # pure attrs
        self.args = list(cmd)
        self.alias = None
        self.binary_loc = None
        self.is_proxy = False
        self.background = False
        self.threadable = True
        self.pipeline_index = None
        self.last_in_pipeline = False
        self.captured_stdout = None
        self.captured_stderr = None
        self.stack = None

    def __str__(self):
        s = self.__class__.__name__ + "(" + str(self.cmd) + ", "
        s += self.cls.__name__ + ", "
        kws = [n + "=" + str(getattr(self, n)) for n in self.kwnames]
        s += ", ".join(kws) + ")"
        return s

    def __repr__(self):
        s = self.__class__.__name__ + "(" + repr(self.cmd) + ", "
        s += self.cls.__name__ + ", "
        kws = [n + "=" + repr(getattr(self, n)) for n in self.kwnames]
        s += ", ".join(kws) + ")"
        return s

    #
    # Properties
    #

    @property
    def stdin(self):
        return self._stdin

    @stdin.setter
    def stdin(self, value):
        if self._stdin is None:
            self._stdin = value
        elif value is None:
            pass
        else:
            safe_close(value)
            msg = "Multiple inputs for stdin for {0!r}"
            msg = msg.format(" ".join(self.args))
            raise XonshError(msg)

    @property
    def stdout(self):
        return self._stdout

    @stdout.setter
    def stdout(self, value):
        if self._stdout is None:
            self._stdout = value
        elif value is None:
            pass
        else:
            safe_close(value)
            msg = "Multiple redirections for stdout for {0!r}"
            msg = msg.format(" ".join(self.args))
            raise XonshError(msg)

    @property
    def stderr(self):
        return self._stderr

    @stderr.setter
    def stderr(self, value):
        if self._stderr is None:
            self._stderr = value
        elif value is None:
            pass
        else:
            safe_close(value)
            msg = "Multiple redirections for stderr for {0!r}"
            msg = msg.format(" ".join(self.args))
            raise XonshError(msg)

    #
    # Execution methods
    #

    def run(self, *, pipeline_group=None):
        """Launches the subprocess and returns the object."""
        event_name = self._cmd_event_name()
        self._pre_run_event_fire(event_name)
        kwargs = {n: getattr(self, n) for n in self.kwnames}
        self.prep_env(kwargs)
        self.prep_preexec_fn(kwargs, pipeline_group=pipeline_group)
        if callable(self.alias):
            if "preexec_fn" in kwargs:
                kwargs.pop("preexec_fn")
            p = self.cls(self.alias, self.cmd, **kwargs)
        else:
            self._fix_null_cmd_bytes()
            p = self._run_binary(kwargs)
        p.spec = self
        p.last_in_pipeline = self.last_in_pipeline
        p.captured_stdout = self.captured_stdout
        p.captured_stderr = self.captured_stderr
        self._post_run_event_fire(event_name, p)
        return p

    def _run_binary(self, kwargs):
        try:
            bufsize = 1
            p = self.cls(self.cmd, bufsize=bufsize, **kwargs)
        except PermissionError:
            e = "xonsh: subprocess mode: permission denied: {0}"
            raise XonshError(e.format(self.cmd[0]))
        except FileNotFoundError:
            cmd0 = self.cmd[0]
            e = "xonsh: subprocess mode: command not found: {0}".format(cmd0)
            env = builtins.__xonsh__.env
            sug = suggest_commands(cmd0, env, builtins.aliases)
            if len(sug.strip()) > 0:
                e += "\n" + suggest_commands(cmd0, env, builtins.aliases)
            raise XonshError(e)
        return p

    def prep_env(self, kwargs):
        """Prepares the environment to use in the subprocess."""
        denv = builtins.__xonsh__.env.detype()
        if ON_WINDOWS:
            # Over write prompt variable as xonsh's $PROMPT does
            # not make much sense for other subprocs
            denv["PROMPT"] = "$P$G"
        kwargs["env"] = denv

    def prep_preexec_fn(self, kwargs, pipeline_group=None):
        """Prepares the 'preexec_fn' keyword argument"""
        if not ON_POSIX:
            return
        if not builtins.__xonsh__.env.get("XONSH_INTERACTIVE"):
            return
        if pipeline_group is None or ON_WSL:
            # If there is no pipeline group
            # or the platform is windows subsystem for linux (WSL)
            xonsh_preexec_fn = no_pg_xonsh_preexec_fn
        else:

            def xonsh_preexec_fn():
                """Preexec function bound to a pipeline group."""
                os.setpgid(0, pipeline_group)
                signal.signal(signal.SIGTSTP, default_signal_pauser)

        kwargs["preexec_fn"] = xonsh_preexec_fn

    def _fix_null_cmd_bytes(self):
        # Popen does not accept null bytes in its input commands.
        # That doesn't stop some subprocesses from using them. Here we
        # escape them just in case.
        cmd = self.cmd
        for i in range(len(cmd)):
            cmd[i] = cmd[i].replace("\0", "\\0")

    def _cmd_event_name(self):
        if callable(self.alias):
            return self.alias.__name__
        elif self.binary_loc is None:
            return "<not-found>"
        else:
            return os.path.basename(self.binary_loc)

    def _pre_run_event_fire(self, name):
        event_name = "on_pre_spec_run_" + name
        if events.exists(event_name):
            event = getattr(events, event_name)
            event.fire(spec=self)

    def _post_run_event_fire(self, name, proc):
        event_name = "on_post_spec_run_" + name
        if events.exists(event_name):
            event = getattr(events, event_name)
            event.fire(spec=self, proc=proc)

    #
    # Building methods
    #

    @classmethod
    def build(kls, cmd, *, cls=subprocess.Popen, **kwargs):
        """Creates an instance of the subprocess command, with any
        modifications and adjustments based on the actual cmd that
        was received.
        """
        # modifications that do not alter cmds may come before creating instance
        spec = kls(cmd, cls=cls, **kwargs)
        # modifications that alter cmds must come after creating instance
        # perform initial redirects
        spec.redirect_leading()
        spec.redirect_trailing()
        # apply aliases
        spec.resolve_alias()
        spec.resolve_binary_loc()
        spec.resolve_auto_cd()
        spec.resolve_executable_commands()
        spec.resolve_alias_cls()
        spec.resolve_stack()
        return spec

    def redirect_leading(self):
        """Manage leading redirects such as with '< input.txt COMMAND'. """
        while len(self.cmd) >= 3 and self.cmd[0] == "<":
            self.stdin = safe_open(self.cmd[1], "r")
            self.cmd = self.cmd[2:]

    def redirect_trailing(self):
        """Manages trailing redirects."""
        while True:
            cmd = self.cmd
            if len(cmd) >= 3 and _is_redirect(cmd[-2]):
                streams = _redirect_streams(cmd[-2], cmd[-1])
                self.stdin, self.stdout, self.stderr = streams
                self.cmd = cmd[:-2]
            elif len(cmd) >= 2 and _is_redirect(cmd[-1]):
                streams = _redirect_streams(cmd[-1])
                self.stdin, self.stdout, self.stderr = streams
                self.cmd = cmd[:-1]
            else:
                break

    def resolve_alias(self):
        """Sets alias in command, if applicable."""
        cmd0 = self.cmd[0]
        if callable(cmd0):
            alias = cmd0
        else:
            alias = builtins.aliases.get(cmd0, None)
        self.alias = alias

    def resolve_binary_loc(self):
        """Sets the binary location"""
        alias = self.alias
        if alias is None:
            binary_loc = locate_binary(self.cmd[0])
        elif callable(alias):
            binary_loc = None
        else:
            binary_loc = locate_binary(alias[0])
        self.binary_loc = binary_loc

    def resolve_auto_cd(self):
        """Implements AUTO_CD functionality."""
        if not (
            self.alias is None
            and self.binary_loc is None
            and len(self.cmd) == 1
            and builtins.__xonsh__.env.get("AUTO_CD")
            and os.path.isdir(self.cmd[0])
        ):
            return
        self.cmd.insert(0, "cd")
        self.alias = builtins.aliases.get("cd", None)

    def resolve_executable_commands(self):
        """Resolve command executables, if applicable."""
        alias = self.alias
        if alias is None:
            pass
        elif callable(alias):
            self.cmd.pop(0)
            return
        else:
            self.cmd = alias + self.cmd[1:]
            # resolve any redirects the aliases may have applied
            self.redirect_leading()
            self.redirect_trailing()
        if self.binary_loc is None:
            return
        try:
            self.cmd = get_script_subproc_command(self.binary_loc, self.cmd[1:])
        except PermissionError:
            e = "xonsh: subprocess mode: permission denied: {0}"
            raise XonshError(e.format(self.cmd[0]))

    def resolve_alias_cls(self):
        """Determine which proxy class to run an alias with."""
        alias = self.alias
        if not callable(alias):
            return
        self.is_proxy = True
        thable = getattr(alias, "__xonsh_threadable__", True)
        cls = ProcProxyThread if thable else ProcProxy
        self.cls = cls
        self.threadable = thable
        # also check capturability, while we are here
        cpable = getattr(alias, "__xonsh_capturable__", self.captured)
        self.captured = cpable

    def resolve_stack(self):
        """Computes the stack for a callable alias's call-site, if needed."""
        if not callable(self.alias):
            return
        # check that we actual need the stack
        sig = inspect.signature(self.alias)
        if len(sig.parameters) <= 5 and "stack" not in sig.parameters:
            return
        # compute the stack, and filter out these build methods
        # run_subproc() is the 4th command in the stack
        # we want to filter out one up, e.g. subproc_captured_hiddenobject()
        # after that the stack from the call site starts.
        stack = inspect.stack(context=0)
        assert stack[3][3] == "run_subproc", "xonsh stack has changed!"
        del stack[:5]
        self.stack = stack


def _safe_pipe_properties(fd, use_tty=False):
    """Makes sure that a pipe file descriptor properties are sane."""
    if not use_tty:
        return
    # due to some weird, long standing issue in Python, PTYs come out
    # replacing newline \n with \r\n. This causes issues for raw unix
    # protocols, like git and ssh, which expect unix line endings.
    # see https://mail.python.org/pipermail/python-list/2013-June/650460.html
    # for more details and the following solution.
    props = termios.tcgetattr(fd)
    props[1] = props[1] & (~termios.ONLCR) | termios.ONLRET
    termios.tcsetattr(fd, termios.TCSANOW, props)


def _update_last_spec(last):
    captured = last.captured
    last.last_in_pipeline = True
    if not captured:
        return
    callable_alias = callable(last.alias)
    if callable_alias:
        pass
    else:
        cmds_cache = builtins.__xonsh__.commands_cache
        thable = cmds_cache.predict_threadable(
            last.args
        ) and cmds_cache.predict_threadable(last.cmd)
        if captured and thable:
            last.cls = PopenThread
        elif not thable:
            # foreground processes should use Popen
            last.threadable = False
            if captured == "object" or captured == "hiddenobject":
                # CommandPipeline objects should not pipe stdout, stderr
                return
    # cannot used PTY pipes for aliases, for some dark reason,
    # and must use normal pipes instead.
    use_tty = ON_POSIX and not callable_alias
    # Do not set standard in! Popen is not a fan of redirections here
    # set standard out
    if last.stdout is not None:
        last.universal_newlines = True
    elif captured in STDOUT_CAPTURE_KINDS:
        last.universal_newlines = False
        r, w = os.pipe()
        last.stdout = safe_open(w, "wb")
        last.captured_stdout = safe_open(r, "rb")
    elif builtins.__xonsh__.stdout_uncaptured is not None:
        last.universal_newlines = True
        last.stdout = builtins.__xonsh__.stdout_uncaptured
        last.captured_stdout = last.stdout
    elif ON_WINDOWS and not callable_alias:
        last.universal_newlines = True
        last.stdout = None  # must truly stream on windows
        last.captured_stdout = ConsoleParallelReader(1)
    else:
        last.universal_newlines = True
        r, w = pty.openpty() if use_tty else os.pipe()
        _safe_pipe_properties(w, use_tty=use_tty)
        last.stdout = safe_open(w, "w")
        _safe_pipe_properties(r, use_tty=use_tty)
        last.captured_stdout = safe_open(r, "r")
    # set standard error
    if last.stderr is not None:
        pass
    elif captured == "object":
        r, w = os.pipe()
        last.stderr = safe_open(w, "w")
        last.captured_stderr = safe_open(r, "r")
    elif builtins.__xonsh__.stderr_uncaptured is not None:
        last.stderr = builtins.__xonsh__.stderr_uncaptured
        last.captured_stderr = last.stderr
    elif ON_WINDOWS and not callable_alias:
        last.universal_newlines = True
        last.stderr = None  # must truly stream on windows
    else:
        r, w = pty.openpty() if use_tty else os.pipe()
        _safe_pipe_properties(w, use_tty=use_tty)
        last.stderr = safe_open(w, "w")
        _safe_pipe_properties(r, use_tty=use_tty)
        last.captured_stderr = safe_open(r, "r")
    # redirect stdout to stderr, if we should
    if isinstance(last.stdout, int) and last.stdout == 2:
        # need to use private interface to avoid duplication.
        last._stdout = last.stderr
    # redirect stderr to stdout, if we should
    if callable_alias and last.stderr == subprocess.STDOUT:
        last._stderr = last.stdout
        last.captured_stderr = last.captured_stdout


def cmds_to_specs(cmds, captured=False):
    """Converts a list of cmds to a list of SubprocSpec objects that are
    ready to be executed.
    """
    # first build the subprocs independently and separate from the redirects
    i = 0
    specs = []
    redirects = []
    for cmd in cmds:
        if isinstance(cmd, str):
            redirects.append(cmd)
        else:
            if cmd[-1] == "&":
                cmd = cmd[:-1]
                redirects.append("&")
            spec = SubprocSpec.build(cmd, captured=captured)
            spec.pipeline_index = i
            specs.append(spec)
            i += 1
    # now modify the subprocs based on the redirects.
    for i, redirect in enumerate(redirects):
        if redirect == "|":
            # these should remain integer file descriptors, and not Python
            # file objects since they connect processes.
            r, w = os.pipe()
            specs[i].stdout = w
            specs[i + 1].stdin = r
        elif redirect == "&" and i == len(redirects) - 1:
            specs[-1].background = True
        else:
            raise XonshError("unrecognized redirect {0!r}".format(redirect))
    # Apply boundary conditions
    _update_last_spec(specs[-1])
    return specs


def _should_set_title(captured=False):
    env = builtins.__xonsh__.env
    return (
        env.get("XONSH_INTERACTIVE")
        and not env.get("XONSH_STORE_STDOUT")
        and captured not in STDOUT_CAPTURE_KINDS
        and builtins.__xonsh__.shell is not None
    )


def run_subproc(cmds, captured=False):
    """Runs a subprocess, in its many forms. This takes a list of 'commands,'
    which may be a list of command line arguments or a string, representing
    a special connecting character.  For example::

        $ ls | grep wakka

    is represented by the following cmds::

        [['ls'], '|', ['grep', 'wakka']]

    Lastly, the captured argument affects only the last real command.
    """
    specs = cmds_to_specs(cmds, captured=captured)
    captured = specs[-1].captured
    if captured == "hiddenobject":
        command = HiddenCommandPipeline(specs)
    else:
        command = CommandPipeline(specs)
    proc = command.proc
    background = command.spec.background
    if not all(x.is_proxy for x in specs):
        add_job(
            {
                "cmds": cmds,
                "pids": [i.pid for i in command.procs],
                "obj": proc,
                "bg": background,
                "pipeline": command,
                "pgrp": command.term_pgid,
            }
        )
    if _should_set_title(captured=captured):
        # set title here to get currently executing command
        pause_call_resume(proc, builtins.__xonsh__.shell.settitle)
    else: