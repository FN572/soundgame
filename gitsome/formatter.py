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
            'ForkEvent': self._format_fork_event,
            'ForkApplyEvent': self._format_general_event,
            'GistEvent': self._format_general_event,
            'GollumEvent': self._format_general_event,
            'IssueCommentEvent': self._format_issue_commment_event,
            'IssuesEvent': self._format_issues_event,
            'MemberEvent': self._format_general_event,
            'MembershipEvent': self._format_general_event,
            'PublicEvent': self._format_general_event,
            'PullRequestEvent': self._format_pull_request_event,
            'PullRequestReviewCommentEvent': self._format_commit_comment_event,
            'PushEvent': self._format_push_event,
            'ReleaseEvent': self._format_release_event,
            'StatusEvent': self._format_general_event,
            'TeamAddEvent': self._format_general_event,
            'RepositoryEvent': self._format_general_event,
            'WatchEvent': self._format_general_event,
        }
        self.pretty_dt = pretty_date_time

    def _format_time(self, event):
        """Format time.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(
            ' (' + str(self.pretty_dt(event.created_at)) + ')',
            fg=self.config.clr_time)
        return item

    def _format_issue_comment(self, event, key):
        """Format an issue comment.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        issue = '{repo[0]}/{repo[1]}#{num}'.format(
            repo=event.payload[key].repository,
            num=event.payload[key].number)
        return click.style(issue, fg=self.config.clr_tertiary)

    def _format_indented_message(self, message, newline=True,
                                 indent='         ', sha=''):
        """Format an indented message.

        :type message: str
        :param message: The commit comment.

        :type newline: bool
        :param newline: Determines whether to prepend a newline.

        :type indent: str
        :param indent: The indent, consisting of blank chars.
            TODO: Consider passing an int denoting # blank chars, or try to
            calculate the indent dynamically.

        :type sha: str
        :param sha: The commit hash.

        :rtype: str
        :return: The formattted commit comment.
        """
        subsequent_indent = indent
        if sha != '':
            subsequent_indent += '         '
        message = self.strip_line_breaks(message)
        formatted_message = click.wrap_text(
            text=click.style(sha, fg=self.config.clr_tertiary)+message,
            initial_indent=indent,
            subsequent_indent=subsequent_indent)
        if newline:
            formatted_message = click.style('\n' + formatted_message)
        return formatted_message

    def _format_sha(self, sha):
        """Format commit hash.

        :type sha: str
        :param sha: The commit hash.
        """
        return sha[:7]

    def _format_commit_comment_event(self, event):
        """Format commit comment and commit hash.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type] + ' ',
                           fg=self.config.clr_secondary)
        item += click.style(
            self._format_sha(event.payload['comment'].commit_id),
            fg=self.config.clr_tertiary)
        item += click.style(' at ', fg=self.config.clr_secondary)
        item += click.style(self.format_user_repo(event.repo),
                            fg=self.config.clr_tertiary)
        try:
            item += click.style(
                '#' + str(event.payload['pull_request'].number) + ' ',
                fg=self.config.clr_tertiary)
        except KeyError:
            pass
        item += self._format_time(event)
        try:
            item += self._format_indented_message(
                event.payload['pull_request'].title)
            item += self._format_indented_message(
                event.payload['comment'].body, indent='           ')
        except KeyError:
            item += self._format_indented_message(
                event.payload['comment'].body)
        return item

    def _format_create_delete_event(self, event):
        """Format a create or delete event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type],
                           fg=self.config.clr_secondary)
        item += click.style(' ' + event.payload['ref_type'],
                            fg=self.config.clr_secondary)
        if event.payload['ref']:
            item += click.style(' ' + event.payload['ref'],
                                fg=self.config.clr_tertiary)
        item += click.style(' at ', fg=self.config.clr_secondary)
        item += click.style(self.format_user_repo(event.repo),
                            fg=self.config.clr_tertiary)
        item += self._format_time(event)
        try:
            item += self._format_indented_message(
                ('' if event.payload['description'] is None
                 else event.payload['description']))
        except KeyError:
            pass
        return item

    def _format_fork_event(self, event):
        """Format a repo fork event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type],
                           fg=self.config.clr_secondary)
        item += click.style(' ' + self.format_user_repo(event.repo),
                            fg=self.config.clr_tertiary)
        item += self._format_time(event)
        return item

    def _format_issue_commment_event(self, event):
        """Format a repo fork event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type] + ' ',
                           fg=self.config.clr_secondary)
        item += self._format_issue_comment(event, key='issue')
        item += self._format_time(event)
        item += self._format_indented_message(
            event.payload['issue'].title)
        item += self._format_indented_message(
            event.payload['comment'].body, indent='           ')
        return item

    def _format_issues_event(self, event):
        """Format an issue event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(event.payload['action'] + ' issue ',
                           fg=self.config.clr_secondary)
        item += self._format_issue_comment(event, key='issue')
        item += self._format_time(event)
        item += self._format_indented_message(
            event.payload['issue'].title)
        return item

    def _format_pull_request_event(self, event):
        """Format a pull request event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(event.payload['action'] + ' pull request ',
                           fg=self.config.clr_secondary)
        item += self._format_issue_comment(event, key='pull_request')
        item += self._format_time(event)
        item += self._format_indented_message(
            event.payload['pull_request'].title)
        return item

    def _format_push_event(self, event):
        """Format a push event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type],
                           fg=self.config.clr_secondary)
        branch = event.payload['ref'].split('/')[-1]
        item += click.style(' ' + branch, fg=self.config.clr_tertiary)
        item += click.style(' at ', fg=self.config.clr_secondary)
        item += click.style(self.format_user_repo(event.repo),
                            fg=self.config.clr_tertiary)
        item += self._format_time(event)
        for commit in event.payload['commits']:
            sha = click.style(self._format_sha(commit['sha']) + ': ',
                              fg=self.config.clr_message)
            item += self._format_indented_message(
                commit['message'], sha=sha)
        return item

    def _format_release_event(self, event):
        """Format a release event.

        :type event: :class:`github3` Event.
        :param event: An instance of `github3` Event.
        """
        item = click.style(self.event_type_mapping[event.type] + ' ',
                           fg=self.config.clr_secondary)
        item += click.style(event.payload['release'].tag_name + ' ',
                            fg=self.config.clr_tertiary)
        item += click.style('at ', fg=self.config.clr_secondary)
        item += click.style(self.format_user_repo(event.repo),
                            fg=self.config.clr_tertiary)
        item += self._format_time(event)
        return item

    def _format_general_event(self, event):
        """Format an event, general case used by various event types.

        :type event: :class:`github3` Event.
        :par