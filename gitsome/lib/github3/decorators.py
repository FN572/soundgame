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
            from .exceptions import error_for
            # Mock a 401 response
            r = generate_fake_error_response(
                '{"message": "Requires authentication"}'
            )
            raise error_for(r)
    return auth_wrapper


def requires_basic_auth(func):
    """Specific (basic) authentication decorator.

    This is used to note which object methods require username/password
    authorization and won't work with token based authorization.

    """
    @wraps(func)
    def auth_wrapper(self, *args, **kwargs):
        if hasattr(self, 'session') and self.session.auth:
            return func(self, *args, **kwargs)
        else:
            from .exceptions import error_for
            # Mock a 401 response
            r = generate_fake_error_response(
                '{"message": "Requires username/password authentication"}'
            )
            raise error_for(r)
    return auth_wrapper


def requires_app_credentials(func):
    """Require client_id and client_secret to be associated.

    This is used to note and enforce which methods require a client_id and
    client_secret to be used.

    """
    @wraps(func)
    def auth_wrapper(self, *args, **kwargs):
        client_id, client_secre