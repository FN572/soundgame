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
        self.tree = None
        if commit.get('tree'):
            self.tree = Tree(commit.get('tree'), self)

    def _repr(self):
        return '<Commit [{0}:{1}]>'.format(self._author_name, self.sha)

    def author_as_User(self):
        """Attempt to return the author attribute as a
        :class:`User <github3.users.User>`. No guarantees are made about the
        validity of this object, i.e., having a login or created_at object.

        """
        return User(self.author, self)

    def committer_as_User(self):
        """Attempt to return the committer attribute as a
        :class:`User <github3.users.User>` object. No guarantees are made
        about the validity of this object.

        """
        return User(self.committer, self)


class Reference(GitHubCore):

    """The :class:`Reference <Reference>` object. This represents a reference
    created on a repository.

    See also: http://developer.github.com/v3/git/refs/

    """

    def _update_attributes(self, ref):
        self._api = ref.get('url', '')
        #: The reference path, e.g., refs/heads/sc/featureA
        self.ref = ref.get('ref')
        #: :class:`GitObject <GitObject>` the reference points to
        self.object = GitObject(ref.get(