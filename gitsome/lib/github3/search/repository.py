# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import GitHubCore
from ..repos import Repository


class RepositorySearchResult(GitHubCore):
    def _update_attributes(self, data):
        result = data.copy()
        #: Score of the resu