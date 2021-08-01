# -*- coding: utf-8 -*-
"""
github3.events
==============

This module contains the class(es) related to Events

"""
from __future__ import unicode_literals

from .models import GitHubCore


class Event(GitHubCore):

    """The :class:`Event <Event>` object. It structures and handles the data
    returned by via the `Events <http://developer.github.com/v3/events>`_
    section of the GitHub API.

    Two events can be compared like so::

        e1 == e2
        e1 != e2

    And that is equivalent to::

        e1.id == e2.id
        e1.id != e2.id

    """

    def _update_attributes(self, event):
        from .users import User
        from .orgs import Organization
        #: :class:`User <github3.users.User>` object representing the actor.
        self.actor = User(event.get('actor')) if event.get('actor') else None
        #: datetime object representing when the event was created.
        self.created_at = self._strptime(event.get('created_at'))
        #: Unique id of the event
        self.id = event.get('id')
        #: List all possible types of Events
        self.org = None
        if event.get('org'):
            self.org = Organization(event.get('org'))
        #: Event type http://developer.github.com/v3/activity/events/types/
        self.type = event.get('type')
        handler = _payload_handlers.get(self.type, identity)
        #: Dictio