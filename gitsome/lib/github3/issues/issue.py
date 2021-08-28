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

