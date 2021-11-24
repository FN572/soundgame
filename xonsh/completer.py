# -*- coding: utf-8 -*-
"""A (tab-)completer for xonsh."""
import builtins
import collections.abc as cabc


class Completer(object):
    """This provides a list of optional completions for the xonsh shell."""