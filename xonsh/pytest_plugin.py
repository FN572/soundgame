# -*- coding: utf-8 -*-
"""Pytest plugin for testing xsh files."""
import sys
import importlib
from traceback import format_list, extract_tb

import pytest

from xonsh.main import setup


def pytest_configure(config):
    setup()


def pytest_collection_modifyitems(items):
    items.sort(key=lambda x: 0 if isinstance(x, XshFunction) else 1)


def _limited_traceback(excinfo):
    """ Return a formatted traceback with all the stack
        from this frame (i.e __file__) up removed
    """
    tb = extract_tb(excinfo.tb)
    try:
        idx = [__file__ in e for e in tb].index(True)
        return format_list(tb[idx + 1 :])
    except ValueError:
        return format_list(tb)


def pytest_collect_file(parent, path):
    if path.ext.lower() == ".xsh" and path.basename.startsw