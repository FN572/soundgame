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
        #: Dictionary with the payload. Payload structure is defined by type_.
        #  _type: http://developer.github.com/v3/events/types
        self.payload = handler(event.get('payload'), self)
        #: Return ``tuple(owner, repository_name)``
        self.repo = event.get('repo')
        if self.repo is not None:
            self.repo = tuple(self.repo['name'].split('/'))
        #: Indicates whether the Event is public or not.
        self.public = event.get('public')

    def _repr(self):
        return '<Event [{0}]>'.format(self.type[:-5])

    @staticmethod
    def list_types():
        """List available payload types."""
        return sorted(_payload_handlers.keys())


def _commitcomment(payload, session):
    from .repos.comment import RepoComment
    if payload.get('comment'):
        payload['comment'] = RepoComment(payload['comment'], session)
    return payload


def _follow(payload, session):
    from .users import User
    if payload.get('target'):
        payload['target'] = User(payload['target'], session)
    return payload


def _forkev(payload, session):
    from .repos import Repository
    if payload.get('forkee'):
        payload['forkee'] = Repository(p