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

        #: Number of comments on this issue.
        self.comments_count = issue.get('comments')
        #: Comments url (not a template)
        self.comments_url = issue.get('comments_url')
        #: datetime object representing when the issue was created.
        self.created_at = self._strptime(issue.get('created_at'))
        #: Events url (not a template)
        self.events_url = issue.get('events_url')
        #: URL to view the issue at GitHub.
        self.html_url = issue.get('html_url')
        #: Unique ID for the issue.
        self.id = issue.get('id')
        #: Returns the list of :class:`Label <github3.issues.label.Label>`\ s
        #: on this issue.
        self.original_labels = [
            Label(l, self) for l in issue.get('labels')
        ]
        labels_url = issue.get('labels_url')
        #: Labels URL Template. Expand with ``name``
        self.labels_urlt = URITemplate(labels_url) if labels_url else None
        #: Locked status
        self.locked = issue.get('locked')
        #: :class:`Milestone <github3.issues.milestone.Milestone>` this
        #: issue was assigned to.
        self.milestone = None
        if issue.get('milestone'):
            self.milestone = Milestone(issue.get('milestone'), self)
        #: Issue number (e.g. #15)
        self.number = issue.get('number')
        #: Dictionary URLs for the pull request (if they exist)
        self.pull_request_urls = issue.get('pull_request', {})
        m = match('https?://[\w\d\-\.\:]+/(\S+)/(\S+)/(?:issues|pull)/\d+',
                  self.html_url)
        #: Returns ('owner', 'repository') this issue was filed on.
        self.repository = m.groups()
        #: State of the issue, e.g., open, closed
        self.state = issue.get('state')
        #: Title of the issue.
        self.title = issue.get('title')
        #: datetime object representing the last time the issue was updated.
        self.updated_at = self._strptime(issue.get('updated_at'))
        #: :class:`User <github3.users.User>` who opened the issue.
        self.user = User(issue.get('user'), self)

        closed_by = issue.get('closed_by')
        #: :class:`User <github3.users.User>` who closed the issue.
        self.closed_by = User(closed_by, self) if closed_by else None

    def _repr(self):
        return '<Issue [{r[0]}/{r[1]} #{n}]>'.format(r=self.repository,
                     