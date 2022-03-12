# -*- coding: utf-8 -*-
"""Implements JSON version of xonsh history backend."""
import os
import sys
import time
import json
import builtins
import collections
import threading
import collections.abc as cabc

from xonsh.history.base import History
import xonsh.tools as xt
import xonsh.lazyjson as xlj
import xonsh.xoreutils.uptime as uptime


def _xhj_gc_commands_to_rmfiles(hsize, files):
    """Return the history files to remove to get under the command limit."""
    rmfiles = []
    n = 0
    ncmds = 0
    for ts, fcmds, f in files[::-1]:
        if fcmds == 0:
            # we need to make sure that 'empty' history files don't hang around
            rmfiles.append((ts, fcmds, f))
        if ncmds + fcmds > hsize:
            break
        ncmds += fcmds
        n += 1
    rmfiles += files[:-n]
    return rmfiles


def _xhj_gc_files_to_rmfiles(hsize, files):
    """Return the history files to remove to get under the file limit."""
    rmfiles = files[:-hsize] if len(files) > hsize else []
    return rmfiles


def _xhj_gc_seconds_to_rmfiles(hsize, files):
    """Return the history files to remove to get under the age limit."""
    rmfiles = []
    now = time.time()
    for ts, _, f in files:
        if (now - ts) < hsize:
            break
        rmfiles.append((None, None, f))
    return rmfiles


def _xhj_gc_bytes_to_rmfiles(hsize, files):
    """Return the history files to remove to get under the byte limit."""
    rmfiles = []
    n = 0
    nbytes = 0
    for _, _, f in files[::-1]:
        fsize = os.stat(f).st_size
        if nbytes + fsize > hsize:
            break
        nbytes += fsize
        n += 1
    rmfiles = files[:-n]
    return rmfiles


def _xhj_get_history_files(sort=True, newest_first=False):
    """Find and return the history files. Optionally sort files by
    modify time.
    """
    data_dir = builtins.__xonsh__.env.get("XONSH_DATA_DIR")
    data_dir = xt.expanduser_abs_path(data_dir)
    try:
        files = [
            os.path.join(data_dir, f)
            for f in os.listdir(data_dir)
            if f.startswith("xonsh-") and f.endswith(".json")
        ]
    except OSError:
        files = []
        if builtins.__xonsh__.env.get("XONSH_DEBUG"):
            xt.print_exception("Could not collect xonsh history files.")
    if sort:
        files.sort(key=lambda x: os.path.getmtime(x), reverse=newest_first)
    return files


class JsonHistoryGC(threading.Thread):
    """Shell history garbage collection."""

    def __init__(self, wait_for_shell=True, size=None, *args, **kwargs):
        """Thread responsible for garbage collecting old history.

        May wait for shell (and for xonshrc to have been loaded) to start work.
        """
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.size = size
        self.wait_for_shell = wait_for_shell
        self.start()
