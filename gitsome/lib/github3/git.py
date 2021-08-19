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

    """The :class:`GitData <GitData>` object. This isn't directly returned to
    the user (developer) ever. This is used to prevent duplication of some
    common items among other Git Data objects.

    """

    def _update_attributes(self, data):
        #: SHA of the object
        self.sha = data.get('sha')
        self._api = data.get('url', '')


class Commit(BaseCommit):

    """The :class:`Commit <Commit>` object. This represents a commit made in a
    repository.

    See also: http://developer.github.com/v3/git/commits/

    """

    def _update_attributes(self, commit):
        super(Commit, self)._update_attributes(commit)
        #: dict containing at least the name, email and date the commit was
        #: created
        self.author = commit.get('author', {}) or {}
        # If GH returns nil/None then make sure author is a dict
        self._author_name = self.author.get('name', '')

        #: dict containing similar information to the author attribute
        self.committer = commit.get('committer', {}) or {}
        # blank the data if GH returns no data

        self._commit_name = self.committer.get('name', '')

        #: :class:`Tree <Tree>` the commit belongs to.
  