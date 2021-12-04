"""Provides completions for xonsh internal utilities"""

import xonsh.xontribs as xx
import xonsh.tools as xt


def complete_xonfig(prefix, line, start, end, ctx):
    """Completion for ``xonfig``"""
    args = line.split(" ")
    if len(args) == 0 or args[0]