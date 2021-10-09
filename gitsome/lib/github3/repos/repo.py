# -*- coding: utf-8 -*-
"""
github3.repos.repo
==================

This module contains the Repository object which is used to access the various
parts of GitHub's Repository API.

"""
from __future__ import unicode_literals

from json import dumps
from base64 import b64encode
from ..decorators import requires_auth
from ..events import Event
from ..git import Blob, Commit, Reference, Tag, Tree
from ..issues import issue_params, Issue
from ..issues.event import IssueEvent
from ..issues.label import Label
from ..issues.milestone import Milestone
from ..models import GitHubCore
from ..notifications import Subscription, Thread
from ..pulls import PullRequest
from .branch import Branch
from .comment import RepoComment
from .commit import RepoCommit
from .comparison import Comparison
from .contents import Contents, validate_commmitter
from .deployment import Deployment
from .hook import Hook
from .issue_import import ImportedIssue
from ..licenses import License
from .pages import PagesBuild, PagesInfo
from .status import Status
from .stats import ContributorStats
from .release import Release, Asset
from .tag import RepoTag
from ..users import User, Key
from ..utils import stream_response_to_file, timestamp_parameter
from uritemplate import URITemplate


class Repository(GitHubCore):

    """The :class:`Repository <Repository>` object.

    It represents how GitHub sends information about repositories.

    Two repository instances can be checked like so::

        r1 == r2
        r1 != r2

    And is equivalent to::

        r1.id == r2.id
        r1.id != r2.id

    See also: http://developer.github.com/v3/repos/

    """

    STAR_HEADERS = {
        'Accept': 'application/vnd.github.v3.star+json'
    }

    def _update_attributes(self, repo):
        #: URL used to clone via HTTPS.
        self.clone_url = repo.get('clone_url', '')
        #: ``datetime`` object representing when the Repository was created.
        self.created_at = self._strptime(repo.get('created_at'))
        #: Description of the repository.
        self.description = repo.get('description', '')

        #: The number of forks of this repository.
        self.forks_count = repo.get('forks_count')
        #: The number of forks of this repository. For backward compatibility
        self.fork_count = self.forks_count

        #: Is this repository a fork?
        self.fork = repo.get('fork')

        #: Full name as login/name
        self.full_name = repo.get('full_name', '')

        # Clone url using git, e.g. git://github.com/sigmavirus24/github3.py
        #: Plain git url for an anonymous clone.
        self.git_url = repo.get('git_url', '')
        #: Whether or not this repository has downloads enabled
        self.has_downloads = repo.get('has_downloads')
        #: Whether or not this repository has an issue tracker
        self.has_issues = repo.get('has_issues')
        #: Whether or not this repository has the wiki enabled
        self.has_wiki = repo.get('has_wiki')

        # e.g. https://sigmavirus24.github.com/github3.py
        #: URL of the home page for the project.
        self.homepage = repo.get('homepage', '')

        #: URL of the pure diff of the pull request
        self.diff_url = repo.get('diff_url', '')

        #: URL of the pure patch of the pull request
        self.patch_url = repo.get('patch_url', '')

        #: API URL of the issue representation of this Pull Request
        self.issue_url = repo.get('issue_url', '')

        # e.g. https://github.com/sigmavirus24/github3.py
        #: URL of the project at GitHub.
        self.html_url = repo.get('html_url', '')
        #: Unique id of the repository.
        self.id = repo.get('id', 0)
        #: Language property.
        self.language = repo.get('language', '')
        #: Mirror property.
        self.mirror_url = repo.get('mirror_url', '')

        # Repository name, 