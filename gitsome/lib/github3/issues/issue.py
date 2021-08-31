# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import match
from json import dumps
from ..decorators import requires_auth
from .comment import IssueComment, issue_comment_params
from .event import IssueEvent
from .label import Label
from .milestone import Milestone
from ..models import GitHubCore
from ..users import User
from uritemplate import URITemplate


class Issue(GitHubCore):

    """The :class:`Issue <Issue>` object. It structures and handles the data
    returned via the `Issues <http://developer.github.com/v3/issues>`_ section
    of the GitHub API.

    Two issue instances can be checked like so::

        i1 == i2
        i1 != i2

    And is equivalent to::

        i1.id == i2.id
        i1.id != i2.id

    """

    # The Accept header will likely be removable once the feature is out of
    # preview mode. See: https://git.io/vgXmB
    LOCKING_PREVIEW_HEADERS = {
        'Accept': 'application/vnd.github.the-key-preview+json'
    }

    def _update_attributes(self, issue):
        self._api = issue.get('url', '')
        #: :class:`User <github3.users.User>` representing the user the issue
        #: was assigned to.
        self.assignee = issue.get('assignee')
        if self.assignee:
            self.assignee = User(issue.get('assignee'), self)
        #: Body (description) of the issue.
        self.body = issue.get('body', '')
        #: HTML formatted body of the issue.
        self.body_html = issue.get('body_html', '')
        #: Plain text formatted body of the issue.
        self.body_text = issue.get('body_text', '')

        # If an issue is still open, this field will be None
        #: datetime object representing when the issue was closed.
        self.closed_at = self._strptime(issue.get('closed_at'))

        #: Numbe