# -*- coding: utf-8 -*-
"""
github3.repos.status
====================

This module contains the Status object for GitHub's commit status API

"""
from __future__ import unicode_literals

from ..models import GitHubCore
from ..users import User


class Status(GitHubCore):
    """The :class:`Status <Status>` object. This represents information from
    the Repo Status API.

    See also: http://developer.github.com/v3/repos/statuses/
    """
    def _update_attributes(self, status):
        #: A string label to differentiate this status from the status of
        #: other systems
        self.context = status.get('context')
        #: datetime object representing the creation of the status object
        self.crea