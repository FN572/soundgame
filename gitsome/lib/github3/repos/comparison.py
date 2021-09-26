# -*- coding: utf-8 -*-
"""
github3.repos.comparison
========================

This module contains the Comparison object for comparing two commits via the
GitHub API.

"""
from __future__ import unicode_literals

from ..models import GitHubCore
from .commit import RepoCommit


class Comparison(GitHubCore):
    """The :class:`Comparison <Comparison>` object. This encapsulates the
    information returned by GitHub comparing two commit objects in a
    repository.

    Two comparison instances can be checked like so::

        c1 == c2
        c1 != c2

    And is equivalent to::

        c1.commits == c2.commits
        c1.commits != c2.commits

    See also:
    http://developer.github.com/v3/repos/commits/#compare-two-commits
    """
    def _update_attributes(self, compare):
        self._api = compare.get('url', '')
        #: URL to view the comparison at GitHub
        self.html_url = compare.get('html_url')
        #: Permanent link to this comparison.
        self.permalink_url = compare.get('permalink_url')
        #: URL to see the diff between the two commits.
        self.diff_url = compare.get('diff_url')
        #: Patch URL at GitHub for the comparison.
        self.patch_url = compare.get('patch_url')
        #: :class:`RepoCommit <github3.repos.commit.RepoCommit>` object
        #: representing the base of comparison.
        self.base_commit = RepoCommit