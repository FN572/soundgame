
"""This module provides the implementation for the retrieving completion results
from bash.
"""
# developer note: this file should not perform any action on import.
#                 This file comes from https://github.com/xonsh/py-bash-completion
#                 and should be edited there!
import os
import re
import sys
import shlex
import shutil
import pathlib
import platform
import functools
import subprocess

__version__ = "0.2.5"


@functools.lru_cache(1)
def _git_for_windows_path():
    """Returns the path to git for windows, if available and None otherwise."""
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\GitForWindows")
        gfwp, _ = winreg.QueryValueEx(key, "InstallPath")
    except FileNotFoundError:
        gfwp = None
    return gfwp


@functools.lru_cache(1)
def _windows_bash_command(env=None):
    """Determines the command for Bash on windows."""
    wbc = "bash"
    path = None if env is None else env.get("PATH", None)
    bash_on_path = shutil.which("bash", path=path)
    if bash_on_path:
        try:
            out = subprocess.check_output(
                [bash_on_path, "--version"],
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError:
            bash_works = False
        else:
            # Check if Bash is from the "Windows Subsystem for Linux" (WSL)
            # which can't be used by xonsh foreign-shell/completer
            bash_works = out and "pc-linux-gnu" not in out.splitlines()[0]

        if bash_works:
            wbc = bash_on_path
        else:
            gfwp = _git_for_windows_path()
            if gfwp:
                bashcmd = os.path.join(gfwp, "bin\\bash.exe")
                if os.path.isfile(bashcmd):
                    wbc = bashcmd
    return wbc


def _bash_command(env=None):
    """Determines the command for Bash on the current plaform."""
    if platform.system() == "Windows":
        bc = _windows_bash_command(env=None)
    else:
        bc = "bash"
    return bc


def _bash_completion_paths_default():
    """A possibly empty tuple with default paths to Bash completions known for
    the current platform.
    """
    platform_sys = platform.system()
    if platform_sys == "Linux" or sys.platform == "cygwin":
        bcd = ("/usr/share/bash-completion/bash_completion",)
    elif platform_sys == "Darwin":
        bcd = (
            "/usr/local/share/bash-completion/bash_completion",  # v2.x
            "/usr/local/etc/bash_completion",
        )  # v1.x
    elif platform_sys == "Windows":
        gfwp = _git_for_windows_path()
        if gfwp:
            bcd = (
                os.path.join(gfwp, "usr\\share\\bash-completion\\" "bash_completion"),
                os.path.join(