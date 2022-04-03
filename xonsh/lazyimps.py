"""Lazy imports that may apply across the xonsh package."""
import importlib

from xonsh.platform import ON_WINDOWS, ON_DARWIN
from xonsh.lazyasd import LazyObject, lazyobject

pygments = LazyObject(
    lambda: importlib.import_module("pygments"), globals(), "pygments"
)
pyghooks = LazyObject(
    lambda: importlib.import_module("xonsh.pyghooks"), globals(), "pyghooks"
)


@lazyobject
def pty():
    if ON_WINDOWS:
        return
    else:
        return importlib.import_module("pty")


@lazyobject
def termios():
    if ON_WINDOWS:
        return
    else:
        return importlib.import_module("termios")


@lazyobject
def fcntl():
    