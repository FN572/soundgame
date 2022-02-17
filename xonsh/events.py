"""
Events for xonsh.

In all likelihood, you want builtins.events

The best way to "declare" an event is something like::

    events.doc('on_spam', "Comes with eggs")
"""
import abc
import builtins
import collections.abc
import inspect

from xonsh.tools import print_exception


def has_kwargs(func):
    return any(
        p.kind == p.VAR_KEYWORD for p in inspect.signature(func).parameters.values()
    )


def debug_level():
    if hasattr(builtins, "__xonsh__") and hasattr(builtins.__xonsh__, "env"):
        return builtins.__xonsh__.env.get("XONSH_DEBUG")
    # FIXME: Under py.test, return 1(?)
    else:
        return 0  # Optimize for speed, not guaranteed correctness


class AbstractEvent(collections.abc.MutableSet, abc.ABC):
    """
    A given event that handlers can register against.

    Acts as a ``MutableSet`` for registered handlers.

    Note that ordering is never guaranteed.
    """

    @property
    def species(self):
        """
        The species (basically, class) of the event
        """
        return type(self).__bases__[
            0
        ]  # events.on_chdir -> <class on_chd