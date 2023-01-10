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
    if spec is None:
        return None
    m = importlib.import_module(spec.name)
    pubnames = getattr(m, "__all__", None)
    if pubnames is not None:
        ctx = {k: getattr(m, k) for k in pubnames}
    else:
        ctx = {k: getattr(m, k) for k in dir(m) if not k.startswith("_")}
    return ctx


def prompt_xontrib_install(names):
    """Returns a formatted string with name of xontrib package to prompt user"""
    md = xontrib_metadata()
    packages = []
    for name in names:
        for xontrib in md["xontribs"]:
            if xontrib["name"] == name:
                packages.append(xontrib["package"])

    print(
        "The following xontribs are enabled but not installed: \n"
        "   {xontribs}\n"
        "To install them run \n"
        "    xpip install {packages}".format(
            xontribs=" ".join(names), packages=" ".join(packages)
        )
    )


def update_context(name, ctx=None):
    """Updates a context in place from a xontrib. If ctx is not provided,
    then __xonsh__.ctx is updated.
    """
    if ctx is None:
        ctx = builtins.__xonsh__.ctx
    if not hasattr(update_context, "bad_imports"):
        update_context.bad_imports = []
    modctx = xontr