# -*- coding: utf-8 -*-
"""
github3.notifications
=====================

This module contains the classes relating to notifications.

See also: http://developer.github.com/v3/activity/notifications/
"""
from __future__ import unicode_literals

from json import dumps
from .models import GitHubCore


class Thread(GitHubCore):
    """The :class:`Thread <Thread>` object wraps notification threads. This
    contains information about the repository generating the notification, the
    subject, and the reason.

    Two thread instances can be checked like so::

        t1 == t2
        t1 != t2

    And is equivalent to::

        t1.id == t2.id
        t1.id != t2.id

    See also:
    http://developer.github.com/v3/activity/notifications/#view-a-single-thread
    """
    def _update_attributes(self, notif):
        self._api = notif.get('url')
        #: Comment responsible for the notification
        self.comment = notif.get('comment', {})
        #: Thread information
        self.thread = notif.get('thread', {})

        from .repos import Repository
        #: Repository the comment was made on
        self.repository = Repository(notif.get('repository', {}), self)
        #: When the thread was last updated
        self.updated_at = self._strptime(notif.get('updated_at'))
        #: Id of the thread
        self.id = notif.get('id')
        #: Dictionary of urls for the thread
        self.urls = notif.get('urls')
        #: datetime object representing the last time the user read the thread
        self.last_read_at = self._strptime(notif.get('last_read_at'))
        #: The reason you're receiving the notification
        self.reason = notif.get('reason')
        #: Subject of the Notification, e.g., which issue/pull/diff is this in
        #: relation to. This is a dictionary
        self.subject = notif.get('subject')
        self.unread = notif.get('unread')

    def _repr(self):
        return '<Thread [{0}]>'.format(self.subject.get('title'))

    def delete_subscription(self):
