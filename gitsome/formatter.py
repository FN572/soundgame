# -*- coding: utf-8 -*-

# Copyright 2015 Donne Martin. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from __future__ import unicode_literals
from __future__ import print_function

import re

from .lib.pretty_date_time import pretty_date_time
import click


class Formatter(object):
    """Handle formatting of isssues, repos, threads, etc.

    :type config: :class:`config.Config`
    :param config: An instance of config.Config.

    :type event_handlers: dict
    :param event_handlers: A mapping of raw event types to format methods.

    :type event_type_mapping: dict
    :param event_type_mapping: A mapping of raw event types to more
        human readable text.

    :type pretty_dt: :class:`pretty_date_time`
    :param pretty_dt: An instance of pretty_date_time.
    """

    def __init__(self, config):
        self.config = config
        self.event_type_mapping = {
            'CommitCommentEvent': 'commented on commit',
            'CreateEvent': 'created',
            'DeleteEvent': 'deleted',
            'FollowEvent': 'followed',
            'ForkEvent': 'forked',
            'GistEvent': 'created/updated gist',
            'GollumEvent': 'created/updated wiki',
            'IssueCommentEvent': 'commented on',
            'IssuesEvent': '',
            'MemberEvent': 'added collaborator',
            'MembershipEvent': 'added/removed user',
            'PublicEvent': 'open sourced',
            'PullRequestEvent': '',
            'PullRequestReviewCommentEvent': 'commented on pull request',
            'PushEvent': 'pushed to',
            'ReleaseEvent': 'released',
            'RepositoryEvent': 'created repository',
            'WatchEvent': 'starred',
        }
        self.event_handlers = {
            'CommitCommentEvent': self._format_commit_comment_event,
            'CreateEvent': self._format_create_delete_event,
            'DeleteEvent': self._format_create_delete_event,
            'FollowEvent': self._format_general_event,
  