# -*- coding: utf-8 -*-
"""
github3.decorators
==================

This module provides decorators to the rest of the library

"""

from functools import wraps
from requests.models import Response
import os

try:  # (No coverage)
    # python2
    from StringIO import StringIO  # (No coverage)
except ImportError:  # (No coverage)
    # python3
    from io import BytesIO as StringIO


class RequestsStringIO(StringIO):
    def read(self, n=-1, *args, **kwargs):
        # StringIO is an old-style class, so can't use super
        return StringIO.read(self, n)


def requires_auth(func):
    """Decorator to note which object methods require authorization."""
    @wraps(func)
    def auth_wrapper(self, *args, **kwargs):
        if hasattr(self, 'session') and self.session.has_auth():
            return func(self, *args, **kwargs)
        else:
            from .exceptions import error