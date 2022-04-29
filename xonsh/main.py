# -*- coding: utf-8 -*-
"""The main xonsh script."""
import os
import sys
import enum
import argparse
import builtins
import contextlib
import signal
import traceback

from xonsh import __version__
from xonsh.timings import setup_timings
from xonsh.lazyasd import lazyobject
from xonsh.shell import Shell
from xonsh.pretty import pretty
from xonsh.execer import Execer
from xonsh.proc import HiddenCommandPipeline
from xonsh.jobs import ignore_sigtstp
from xonsh.tools import setup_win_unicode_console, print_color, to_bool_or_int
from xonsh.platform import HAS_PYGMENTS, ON_WINDOWS
from xonsh.codecache import run_script_with_cache, run_code_with_cache
from xonsh.xonfig import print_welcome_screen
from xonsh.xontribs import xontribs_load
from xonsh.lazyimps import pygments, pyghooks
from xonsh.imphooks import install_import_hooks
from xonsh.events import events
from xonsh.environ import xonshrc_context, make_args_env
from xonsh.built_ins import XonshSession, load_builtins, load_proxies

from gitsome import __version__ as gitsome_version


events.transmogrify("on_post_init", "LoadEvent")
events.doc(
    "on_post_init",
    """
on_post_init() -> None

Fired after all initialization is finished and we're ready to do work.

NOTE: This is fired before the wizard is automatically started.
""",
)

events.transmogrify("on_exit", "LoadEvent")
events.doc(
    "on_exit",
    """
on_exit() -> None

Fired after all commands have been executed, before tear-down occurs.

NOTE: All the caveats of the ``atexit`` module also apply to this event.
""",
)


events.transmogrify("on_pre_cmdloop", "LoadEvent")
events.doc(
    "on_pre_cmdloop",
    """
on_pre_cmdloop() -> None

Fired just before the command loop is started, if it is.
""",
)

events.transmogrify("on_post_cmdloop", "LoadEvent")
events.doc(
    "on_post_cmdloop",
    """
on_post_cmdloop() -> None

Fired just after the command loop finishes, if it is.

NOTE: All the caveats of the ``atexit`` module also apply to this event.
""",
)

events.transmogrify("on_pre_rc", "LoadEvent")
events.doc(
    "on_pre_rc",
    """
on_pre_rc() -> None

Fired just before rc files are loaded, if they are.
""",
)

events.transmogrify("on_post_rc", "LoadEvent")
events.doc(
    "on_post_rc",
    """
on_post_rc() -> None

Fired just after rc files are loaded, if they are.
""",
)


def get_setproctitle():
    """Proxy function for loading process title"""
    try:
        from setproctitle import setproctitle as spt
    except ImportError:
        return
    return spt


def path_argument(s):
    """Return a path only if the path is actually legal

    This is very similar to argparse.FileType, except that it doesn't return
    an open file handle, but rather simply validates the path."""

    s = os.path.abspath(os.path.expanduser(s))
    if not os.path.isfile(s):
        msg = "{0!r} must be a valid path to a file".format(s)
        raise argparse.ArgumentTypeError(msg)
    return s


@lazyobject
def parser():
    p = argparse.ArgumentParser(description="xonsh", add_help=False)
    p.add_argument(
        "-h",
        "--help",
        dest="help",
        action="store_true",
        default=False,
        help="show help and exit",
    )
    p.add_argument(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="show version information and exit",
    )
    p.add_argument(
        "-c",
        help="Run a single command and exit",
        dest="command",
        required=False,
        default=None,
    )
    p.add_argument(
        "-i",
        "--interactive",
        help="force running in interactive mode",
        dest="force_interactive",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "-l",
        "--login",
        help="run as a login shell",
        dest="login",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "--config-path",
        help="DEPRECATED: static configuration files may now be used "
        "in the XONSHRC file list, see the --rc option.",
        dest="config_path",
        default=None,
        type=path_argument,
    )
    p.add_argument(
        "--rc",
        help="The xonshrc files to load, these may be either xonsh "
        "files or JSON-based static configuration files.",
        dest="rc",
        nargs="+",
        type=path_argument,
        default=None,
    )
    p.add_argument(
        "--no-rc",
        help="Do not load the .xonshrc files",
        dest="norc",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "--no-script-cache",
        help="Do not cache scripts as they are run",
        dest="scriptcache",
        action="store_false",
        default=True,
    )
    p.add_argument(
        "--cache-everything",
        help="Use a cache, even for interactive commands",
        dest="cacheall",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "-D",
        dest="defines",
        help="define an environment variable, in the form of "
        "-DNAME=VAL. May be used many times.",
        metavar="ITEM",
        action="append",
        default=None,
    )
    p.add_argument(
        "--shell-type",
        help="What kind of shell should be used. "
        "Possible options: readline, prompt_toolkit, random. "
        "Warning! If set this overrides $SHELL_TYPE variable.",
        dest="shell_type",
        choices=tuple(Shell.shell_type_aliases.keys()),
        default=None,
    )
    p.add_argument(
        "--timings",
        help="Prints timing information before the prompt is shown. "
        "This is useful while tracking down performance issues "
        "and investigating startup times.",
        dest="timings",
        action="store_true",
        default=None,
    )
    p.add_argument(
        "file",
        metavar="script-file",
        help="If present, execute the script in script-file" " and exit",
        nargs="?",
        default=None,
    )
    p.add_argument(
        "args",
        metavar="args",
        help="Additional arguments to the script specified " "by script-file",
        nargs=argparse.REMAINDER,
        default=[],
    )
    return p


def _pprint_displayhook(value):
    if value is None:
        return
    builtins._ = None  # Set '_' to None to avoid recursion
    if isinstance(value, HiddenCommandPipeline):
        builtins._ = value
        return
    env = builtins.__xonsh__.env
    if env.get("PRETTY_PRINT_RESULTS"):
        printed_val = pretty(value)
    else:
        printed_val = repr(value)
    if HAS_PYGMENTS and env.get("COLOR_RESULTS"):
        tokens = list(pygments.lex(printed_val, lexer=pyghooks.XonshLexer()))
        end = "" if env.get("SHELL_TYPE") == "prompt_toolkit2" else "\n"
        print_color(tokens, end=end)
    else:
        print(printed_val)  # black & white case
    builtins._ = value


class XonshMode(enum.Enum):
    single_command = 0
    script_from_file = 1
    script_from_stdin = 2
    interactive = 3


def start_services(shell_kwargs, args):
    """Starts up the essential services in the proper order.
    This returns the environment instance as a convenience.
    """
    install_import_hooks()
    # create execer, which loads builtins
    ctx = shell_kwargs.get("ctx", {})
    debug = to_bool_or_int(os.getenv("XONSH_DEBUG", "0"))
    events.on_timingprobe.fire(name="pre_execer_init")
    execer = Execer(
        xonsh_ctx=ctx,
        debug_level=debug,
        scriptcache=shell_kwargs.get("scriptcache", True),
        cacheall=shell_kwargs.get("cacheall", False),
    )
    events.on_timingprobe.fire(name="post_execer_init")
    # load rc files
    login = shell_kwargs.get("login", True)
    env = builtins.__xonsh__.env
    rc = shell_kwargs.get("rc", None)
    rc = env.get("XONSHRC") if rc is None else rc
    if args.mode != XonshMode.interactive and not args.force_interactive:
        #  Don't load xonshrc if not interactive shell
        rc = None
    events.on_pre_rc.fire()
    xonshrc_context(rcfiles=rc, execer=e