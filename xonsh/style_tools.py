
"""Xonsh color styling tools that simulate pygments, when it is unavailable."""
import builtins
from collections import defaultdict

from xonsh.platform import HAS_PYGMENTS
from xonsh.lazyasd import LazyObject
from xonsh.color_tools import RE_BACKGROUND
from xonsh.tools import FORMATTER


class _TokenType(tuple):
    """
    Forked from the pygments project
    https://bitbucket.org/birkenfeld/pygments-main
    Copyright (c) 2006-2017 by the respective authors, All rights reserved.
    See https://bitbucket.org/birkenfeld/pygments-main/raw/05818a4ef9891d9ac22c851f7b3ea4b4fce460ab/AUTHORS
    """

    parent = None

    def split(self):
        buf = []
        node = self
        while node is not None:
            buf.append(node)
            node = node.parent
        buf.reverse()
        return buf

    def __init__(self, *args):
        # no need to call super.__init__
        self.subtypes = set()

    def __contains__(self, val):
        return self is val or (type(val) is self.__class__ and val[: len(self)] == self)

    def __getattr__(self, val):
        if not val or not val[0].isupper():
            return tuple.__getattribute__(self, val)
        new = _TokenType(self + (val,))
        setattr(self, val, new)
        self.subtypes.add(new)
        new.parent = self
        return new

    def __repr__(self):