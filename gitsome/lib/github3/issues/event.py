# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import GitHubCore
from ..users import User


class IssueEvent(GitHubCore):
    """The :class:`IssueEvent <IssueEvent>` object. This specifically deals
    with events described in the
    `Issues\>Events <http://developer.github.com/v3/issues/events>`_ section of
    the GitHub API.

    Two event instances can be checked like so::

        e1 == e2
        e1 != e2

    And is equivalent to::

        e1.commit_id == e2.commit_id
        e1.commit_id != e2.commit_id

    """
    def _update_attributes(self, event):
        # The type of event:
        #   ('closed', 'reopened', 'subscribed', 'merged', 'referenced',
        #    'mentioned', 'assigned')
        #: The type of event, e.g., closed
        self.event = event.get