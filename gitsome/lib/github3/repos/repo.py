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

        # Repository name, e.g. github3.py
        #: Name of the repository.
        self.name = repo.get('name', '')

        #: Number of open issues on the repository. DEPRECATED
        self.open_issues = repo.get('open_issues', 0)

        #: Number of open issues on the repository
        self.open_issues_count = repo.get('open_issues_count')

        # Repository owner's name
        #: :class:`User <github3.users.User>` object representing the
        #: repository owner.
        self.owner = User(repo.get('owner', {}), self)

        #: Is this repository private?
        self.private = repo.get('private')

        #: Permissions for this repository
        self.permissions = repo.get('permissions')

        #: ``datetime`` object representing the last time commits were pushed
        #: to the repository.
        self.pushed_at = self._strptime(repo.get('pushed_at'))
        #: Size of the repository.
        self.size = repo.get('size', 0)

        # The number of stargazers
        #: Number of users who starred the repository
        self.stargazers_count = repo.get('stargazers_count', 0)

        #: ``datetime`` object representing when the repository was starred
        self.starred_at = self._strptime(repo.get('starred_at'))

        # SSH url e.g. git@github.com/sigmavirus24/github3.py
        #: URL to clone the repository via SSH.
        self.ssh_url = repo.get('ssh_url', '')
        #: If it exists, url to clone the repository via SVN.
        self.svn_url = repo.get('svn_url', '')
        #: ``datetime`` object representing the last time the repository was
        #: updated.
        self.updated_at = self._strptime(repo.get('updated_at'))
        self._api = repo.get('url', '')

        # The number of watchers
        #: Number of users watching the repository.
        self.watchers = repo.get('watchers', 0)

        #: Parent of this fork, if it exists :class:`Repository`
        self.source = repo.get('source')
        if self.source:
            self.source = Repository(self.source, self)

        #: Parent of this fork, if it exists :class:`Repository`
        self.parent = repo.get('parent')
        if self.parent:
            self.parent = Repository(self.parent, self)

        #: default branch for the repository
        self.default_branch = repo.get('default_branch', '')

        #: master (default) branch for the repository
        self.master_branch = repo.get('master_branch', '')

        #: Teams url (not a template)
        self.teams_url = repo.get('teams_url', '')

        #: Hooks url (not a template)
        self.hooks_url = repo.get('hooks_url', '')

        #: Events url (not a template)
        self.events_url = repo.get('events_url', '')

        #: Tags url (not a template)
        self.tags_url = repo.get('tags_url', '')

        #: Languages url (not a template)
        self.languages_url = repo.get('languages_url', '')

        #: Stargazers url (not a template)
        self.stargazers_url = repo.get('stargazers_url', '')

        #: Contributors url (not a template)
        self.contributors_url = repo.get('contributors_url', '')

        #: Subscribers url (not a template)
        self.subscribers_url = repo.get('subscribers_url', '')

        #: Subscription url (not a template)
        self.subscription_url = repo.get('subscription_url', '')

        #: Merges url (not a template)
        self.merges_url = repo.get('merges_url', '')

        #: Downloads url (not a template)
        self.download_url = repo.get('downloads_url', '')

        # Template URLS
        ie_url_t = repo.get('issue_event