import os
import re
import pickle
import builtins
import subprocess

import xonsh.lazyasd as xl

from xonsh.completers.tools import get_filter_function

OPTIONS = None
OPTIONS_PATH = None


@xl.lazyobject
def SCRAPE_RE():
    return re.compile(r"^(?:\s*(?:-\w|--[a-z0-9-]+)[\s,])+", re.M)


@xl.lazyobject
def INNER_OPTIONS_RE():
    return re.compile(r"-\w|--[a-z0-9-]+")


def complete_from_man(prefix, line, start, end, ctx):
    """
    Completes an option name, based on the contents of the associated man
    page.
    """
    global OPTIONS, OPTIONS_PATH
    if OPTIONS is None:
        datadir = builtins.__xonsh_