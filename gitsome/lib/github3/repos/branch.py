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

  