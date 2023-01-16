"""Implements the which xoreutil."""
import os
import argparse
import builtins
import functools

from xonsh.xoreutils import _which
import xonsh.platform as xp
import xonsh.proc as xproc


@functools.lru_cache()
def _which_create_parser():
    desc = "Parses arguments to which wrapper"
    parser = argparse.ArgumentParser("which", description=desc)
    parser.add_argument(
        "args", type=str, nargs="+", help="The executables or aliases to search for"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        dest="all",
        help="Show all matches in globals, xonsh.aliases, $PATH",
    )
    parser.add_argument(
        "-s",
        "--skip-alias",
        action="store_true",
        help="Do not search inxonsh.aliases",
        dest="skip",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="{}".format(_which.__version__),
        help="Display the version of the python which module " "used by xonsh",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Print out how matches were located and show " "near misses on stderr",
    )
    parser.add_argument(
        "-