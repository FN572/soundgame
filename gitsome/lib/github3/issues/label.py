# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import dumps
from ..decorators import requires_auth
from ..models import GitHubCore


class Label(GitHubCore):
    """The :class:`Label <Label>` object. Succintly represents a label that
    exists in a repository.

    See also: http://developer.github.com/v3/issues/labels/
    """
    def _update_attributes(self, label):
        self._api = label.get('url', '')
        #: Color of the label, e.g., 626262
        self.color = label.get('color')
        #: Name of the label, e.g., 'bug'
        self.name = label.get('name')

        self._uniq = self._api

    def _repr(self)