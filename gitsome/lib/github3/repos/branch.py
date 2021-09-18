# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import dumps
from ..models import GitHubCore
from .commit import RepoCommit


class Branch(GitHubCore):
    """The :class:`Branch <Branch>` object. It holds the information GitHub
    returns about a branch on a
    :class:`Repository <github3.repos.repo.Repository>`.
    """

    # The Accept header will likely be removable once the feature is out of
    # preview mode. See: http://git.io/v4O1e
    PREVIEW_HEADERS = {'Accept': 'application/vnd.github.loki-preview+json'}

    def _update_attributes(self, branch):
        #: Name of the branch.
        self.name = branch.get('name')
        #: Returns the branch's
        #: :class:`RepoCommit <github3.repos.commit.RepoCommit>` or ``None``.
        self.commit = branch.get('commit')
        if self.commit:
            self.commit = RepoCommit(self.commit, self)
        #: Returns '_links' attribute.
        self.links = branch.get('_links', {})
        #: Provides the branch's protection status.
        self.protection = branch.get('protection')

        if 'self' in self.links:
            self._api = self.links['self']
        else:  # Branches obtained via `repo.branches` don't have links.
            base = self.commit.url.split('/commit', 1)[0]
            self._api = self._build_url('branches', self.name, base_url=base)

    def _repr(self):
        return '<Repository Branch [{0}]>'.format(self.name)

    def latest_sha(self, differs_from=''):
        """Check if SHA-1 is the same as re