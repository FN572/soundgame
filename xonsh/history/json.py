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
    for ts, fcm