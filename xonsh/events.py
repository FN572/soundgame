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
        ]  # events.on_chdir -> <class on_chdir> -> <class Event>

    def __call__(self, handler):
        """
        Registers a handler. It's suggested to use this as a decorator.

        A decorator method is added to the handler, validator(). If a validator
        function is added, it can filter if the handler will be considered. The
        validator takes the same arguments as the handler. If it returns False,
        the handler will not called or considered, as if it was not registered
        at all.

        Parameters
        ----------
        handler : callable
            The handler to register

        Returns
        -------
        rtn : callable
            The handler
        """
        #  Using Python's "private" munging to minimize hypothetical collisions
        handler.__validator = None
        if debug_level():
            if not has_kwargs(handler):
                raise ValueError("Event handlers need a **kwargs for future proofing")
        self.add(handler)

        def validator(vfunc):
            """
            Adds a validator function to a handler to limit when it is considered.
            """
            if debug_level():
                if not has_kwargs(handler):
                    raise ValueError(
                        "Event validators need a **kwargs for future proofing"
                    )
            handler.__validator = vfunc

        handler.validator = validator

        return handler

    def _filterhandlers(self, handlers, **kwargs):
        """
        Helper method for implementing classes. Generates the handlers that pass validation.
        """
        for handler in handlers:
            if handler.__validator is not None and not handler.__validator(**kwargs):
                continue
            yield handler

    @abc.abstractmethod
    def fire(self, **kwargs):
        """
        Fires an event, calling registered handlers with the given arguments.

        Parameters
        ----------
        **kwargs :
            Keyword arguments to pass to each handler
        """


class Event(AbstractEvent):
    """
    An event species for notify and scatter-gather events.
    """

    # Wish I could just pull from set...
    def __init__(self):
        self._handlers = set()
        self._firing = False