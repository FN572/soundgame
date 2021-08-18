# -*- coding: utf-8 -*-
"""
github3.git
===========

This module contains all the classes relating to Git Data.

See also: http://developer.github.com/v3/git/
"""
from __future__ import unicode_literals

from json import dumps
from base64 import b64decode
from .models import GitHubCore, BaseCommit
from .users import User
from .decorators import requires_auth


class Blob(GitHubCore):

    """The :class:`Blob <Blob>` object.

    See also: http://developer.github.com/v3/git/blobs/

    """

    def _update_attributes(self, blob):
        self._api = blob.get('url', '')

        #: Raw content of the blob.
        self.content = blob.get('content').encode()

        #: Encoding of the raw content.
        self.encoding = blob.get('encoding')

        #: Decoded content of the blob.
        self.decoded = self.content
        if self.encoding == 'base64':
            self.decoded = b64decode(self.content)

        #: Size of the blob in bytes
        self.size = blob.get('size')
        #: SHA1 of the blob
        self.sha = blob.get('sha')

    def _repr(self):
        return '<Blob [{0:.10}]>'.format(self.sha)


class GitData(GitHubCore):

  