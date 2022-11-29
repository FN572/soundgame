# -*- coding: utf-8 -*-
"""CWD related prompt formatter"""

import os
import shutil
import builtins

import xonsh.tools as xt
import xonsh.platform as xp


def _replace_home(x):
    if xp.ON_WINDOWS:
        home = (
            builtins.__xonsh__.env["HOMEDRIVE"] + builtins.__xonsh__.env["HOMEPATH"][0]
        )
        if x.startswith(home):
            x = x.replace(home, "~", 1)

        if builtins.__xonsh__.env.get("FORCE_POSIX_PATHS"):
            x = x.replace(os.sep, os.altsep)

        return x
    else:
        home = builtins.__xonsh__.env["HOME"]
        if x.startswith(home):
            x = x.replace(home, "~", 1)
        return x


def _replace_home_cwd():
    return _replace_home(builtins.__xonsh__.env["PWD"])


def _collapsed_pwd():
    sep = xt.get_sep()
    pwd = _replace_home_cwd().split(sep)
    l = len(pwd)
    leader = sep if l > 0 and len(pwd[0]) == 0 else ""
    base = [
        i[0] if ix != l - 1 and i[0] != "." else i[0:2] if ix != l - 1 else i
        for ix, i in enumerate(pwd)
        if len(i) > 0
    ]
    return leader + sep.join(base)


def _dynamically_collapsed_pwd():
    """Return the compact current working directory.  It respects the
    environment variable DYNAMIC_CWD_WIDTH.
    """
    original_path = _replace_home_cwd()
    target_