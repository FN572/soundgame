
# -*- coding: utf-8 -*-
"""
github3.models
==============

This module provides the basic models used in github3.py

"""
from __future__ import unicode_literals

from json import dumps, loads
from requests.compat import urlparse, is_py2
from datetime import datetime
from logging import getLogger

from . import exceptions
from .decorators import requires_auth
from .null import NullObject
from .session import GitHubSession
from .utils import UTC

__timeformat__ = '%Y-%m-%dT%H:%M:%SZ'
__logs__ = getLogger(__package__)


class GitHubCore(object):

    """The base object for all objects that require a session.

    The :class:`GitHubCore <GitHubCore>` object provides some
    basic attributes and methods to other sub-classes that are very useful to
    have.
    """

    def __init__(self, json, session=None):
        if hasattr(session, 'session'):
            # i.e. session is actually a GitHubCore instance
            session = session.session
        elif session is None:
            session = GitHubSession()
        self.session = session

        # set a sane default
        self._github_url = 'https://api.github.com'

        if json is not None:
            self.etag = json.pop('ETag', None)
            self.last_modified = json.pop('Last-Modified', None)
            self._uniq = json.get('url', None)
        self._json_data = json
        self._update_attributes(json)

    def _update_attributes(self, json):
        pass

    def __getattr__(self, attribute):
        """Proxy access to stored JSON."""
        if attribute not in self._json_data:
            raise AttributeError(attribute)
        value = self._json_data.get(attribute, None)
        setattr(self, attribute, value)
        return value

    def as_dict(self):
        """Return the attributes for this object as a dictionary.

        This is equivalent to calling::

            json.loads(obj.as_json())

        :returns: this object's attributes serialized to a dictionary
        :rtype: dict
        """
        return self._json_data

    def as_json(self):
        """Return the json data for this object.

        This is equivalent to calling::

            json.dumps(obj.as_dict())

        :returns: this object's attributes as a JSON string
        :rtype: str
        """
        return dumps(self._json_data)

    def _strptime(self, time_str):
        """Convert an ISO 8601 formatted string to a datetime object.

        We assume that the ISO 8601 formatted string is in UTC and we create
        the datetime object so that it is timezone-aware.

        :param str time_str: ISO 8601 formatted string
        :returns: timezone-aware datetime object
        :rtype: datetime or None
        """
        if time_str:
            # Parse UTC string into naive datetime, then add timezone
            dt = datetime.strptime(time_str, __timeformat__)
            return dt.replace(tzinfo=UTC())
        return None

    def __repr__(self):
        repr_string = self._repr()
        if is_py2:
            return repr_string.encode('utf-8')
        return repr_string

    @classmethod
    def from_dict(cls, json_dict):
        """Return an instance of this class formed from ``json_dict``."""
        return cls(json_dict)

    @classmethod
    def from_json(cls, json):
        """Return an instance of this class formed from ``json``."""
        return cls(loads(json))

    def __eq__(self, other):
        return self._uniq == other._uniq

    def __ne__(self, other):
        return self._uniq != other._uniq

    def __hash__(self):
        return hash(self._uniq)

    def _repr(self):
        return '<github3-core at 0x{0:x}>'.format(id(self))

    @staticmethod
    def _remove_none(data):
        if not data:
            return
        for (k, v) in list(data.items()):
            if v is None:
                del(data[k])

    def _instance_or_null(self, instance_class, json):
        if json is None:
            return NullObject(instance_class.__name__)
        if not isinstance(json, dict):
            return exceptions.UnprocessableResponseBody(
                "GitHub's API returned a body that could not be handled", json
            )
        try:
            return instance_class(json, self)
        except TypeError:  # instance_class is not a subclass of GitHubCore
            return instance_class(json)