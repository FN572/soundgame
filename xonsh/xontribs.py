"""Tools for helping manage xontributions."""
import os
import sys
import json
import builtins
import argparse
import functools
import importlib
import importlib.util

from xonsh.tools import print_color, unthreadable


@functools.lru_cache(1)
def xontribs_json():
    return os.path.join(os.path.dirname(__file__), "xontribs.json")


def find_xontrib(name):
    """Finds a xontribution from its name."""
    if name.startswith("."):
        spec = importlib.util.find_spec(name, package="xontrib")
    else:
        spec = importlib.util.find_spec("." + name, package="xontrib")
    return spec or importlib.util.find_spec(name)


def xontrib_context(name):
    """Return a context dictionary for a xontrib of a given name."""
    spec = find_xontrib(name)
  