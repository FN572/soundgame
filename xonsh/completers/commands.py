import os
import builtins

import xonsh.tools as xt
import xonsh.platform as xp

from xonsh.completers.tools import get_filter_function

SKIP_TOKENS = {"sudo", "time", "timeit", "which", "showcmd", "man"}
END_PROC_TOKENS = {"|", "||", "&&", "and", "or"}


def complete_command(cmd, line, start, end, ctx):
    """
    Returns a list of valid commands starting with the first argument
    """
    space = " "
    out = {
        s + space
        for s in builtins.__xonsh__.commands_cache
        if get_filter_function()(s, cmd)
    }
    if xp.ON_WINDOWS:
        out |= {i for i in xt.executables_in(".") if i.startswith(cmd)}
    base = os.path.basename(cmd)
    if os.path.isdir(base):
        out |= {
            os.path.join(base, i) for i in xt.executables_in(base) if i.starts