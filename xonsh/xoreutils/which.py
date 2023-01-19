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
        "-p",
        "--plain",
        action="store_true",
        dest="plain",
        help="Do not display alias expansions or location of "
        "where binaries are found. This is the "
        "default behavior, but the option can be used to "
        "override the --verbose option",
    )
    parser.add_argument("--very-small-rocks", action=AWitchAWitch)
    if xp.ON_WINDOWS:
        parser.add_argument(
            "-e",
            "--exts",
            nargs="*",
            type=str,
            help="Specify a list of extensions to use instead "
            "of the standard list for this system. This can "
            "effectively be used as an optimization to, for "
            'example, avoid stat\'s of "foo.vbs" when '
            'searching for "foo" and you know it is not a '
            'VisualBasic script but ".vbs" is on PATHEXT. '
            "This option is only supported on Windows",
            dest="exts",
        )
    return parser


def print_global_object(arg, stdout):
    """Print the object."""
    obj = builtins.__xonsh__.ctx.get(arg)
    print("global object of {}".format(type(obj)), file=stdout)


def print_path(abs_name, from_