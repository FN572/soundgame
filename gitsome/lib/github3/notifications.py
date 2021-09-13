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
        #: Comm