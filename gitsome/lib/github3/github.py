
# -*- coding: utf-8 -*-
"""
github3.github
==============

This module contains the main GitHub session object.

"""
from __future__ import unicode_literals

import json

from .auths import Authorization
from .decorators import (requires_auth, requires_basic_auth,
                         requires_app_credentials)
from .events import Event
from .gists import Gist
from .issues import Issue, issue_params
from .models import GitHubCore
from .orgs import Membership, Organization, Team
from .pulls import PullRequest
from .repos.repo import Repository, repo_issue_params
from .search import (CodeSearchResult, IssueSearchResult,
                     RepositorySearchResult, UserSearchResult)
from .structs import SearchIterator
from . import users
from .notifications import Thread
from .licenses import License
from uritemplate import URITemplate


class GitHub(GitHubCore):

    """Stores all the session information.

    There are two ways to log into the GitHub API

    ::

        from github3 import login
        g = login(user, password)
        g = login(token=token)
        g = login(user, token=token)

    or

    ::

        from github3 import GitHub
        g = GitHub(user, password)
        g = GitHub(token=token)
        g = GitHub(user, token=token)

    This is simple backward compatibility since originally there was no way to
    call the GitHub object with authentication parameters.
    """

    def __init__(self, username='', password='', token=''):
        super(GitHub, self).__init__({})
        if token:
            self.login(username, token=token)
        elif username and password:
            self.login(username, password)

    def _repr(self):
        if self.session.auth:
            return '<GitHub [{0[0]}]>'.format(self.session.auth)
        return '<GitHub at 0x{0:x}>'.format(id(self))

    @requires_auth
    def add_email_addresses(self, addresses=[]):
        """Add the email addresses in ``addresses`` to the authenticated
        user's account.

        :param list addresses: (optional), email addresses to be added
        :returns: list of :class:`~github3.users.Email`
        """
        json = []
        if addresses:
            url = self._build_url('user', 'emails')
            json = self._json(self._post(url, data=addresses), 201)
        return [users.Email(email) for email in json] if json else []

    def all_events(self, number=-1, etag=None):
        """Iterate over public events.

        :param int number: (optional), number of events to return. Default: -1
            returns all available events
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of :class:`Event <github3.events.Event>`\ s
        """
        url = self._build_url('events')
        return self._iter(int(number), url, Event, etag=etag)

    def all_organizations(self, number=-1, since=None, etag=None,
                          per_page=None):
        """Iterate over every organization in the order they were created.

        :param int number: (optional), number of organizations to return.
            Default: -1, returns all of them
        :param int since: (optional), last organization id seen (allows
            restarting this iteration)
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :param int per_page: (optional), number of organizations to list per
            request
        :returns: generator of :class:`Organization
            <github3.orgs.Organization>`
        """
        url = self._build_url('organizations')
        return self._iter(int(number), url, Organization,
                          params={'since': since, 'per_page': per_page},
                          etag=etag)

    def all_repositories(self, number=-1, since=None, etag=None,
                         per_page=None):
        """Iterate over every repository in the order they were created.

        :param int number: (optional), number of repositories to return.
            Default: -1, returns all of them
        :param int since: (optional), last repository id seen (allows
            restarting this iteration)
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :param int per_page: (optional), number of repositories to list per
            request
        :returns: generator of :class:`Repository <github3.repos.Repository>`
        """
        url = self._build_url('repositories')
        return self._iter(int(number), url, Repository,
                          params={'since': since, 'per_page': per_page},
                          etag=etag)

    def all_users(self, number=-1, etag=None, per_page=None, since=None):
        """Iterate over every user in the order they signed up for GitHub.

        .. versionchanged:: 1.0.0

            Inserted the ``since`` parameter after the ``number`` parameter.

        :param int number: (optional), number of users to return. Default: -1,
            returns all of them
        :param int since: (optional), ID of the last user that you've seen.
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :param int per_page: (optional), number of users to list per request
        :returns: generator of :class:`User <github3.users.User>`
        """
        url = self._build_url('users')
        return self._iter(int(number), url, users.User, etag=etag,
                          params={'per_page': per_page, 'since': since})

    @requires_basic_auth
    def authorization(self, id_num):
        """Get information about authorization ``id``.

        :param int id_num: (required), unique id of the authorization
        :returns: :class:`Authorization <Authorization>`
        """
        json = None
        if int(id_num) > 0:
            url = self._build_url('authorizations', str(id_num))
            json = self._json(self._get(url), 200)
        return self._instance_or_null(Authorization, json)

    @requires_basic_auth
    def authorizations(self, number=-1, etag=None):
        """Iterate over authorizations for the authenticated user. This will
        return a 404 if you are using a token for authentication.

        :param int number: (optional), number of authorizations to return.
            Default: -1 returns all available authorizations
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of :class:`Authorization <Authorization>`\ s
        """
        url = self._build_url('authorizations')
        return self._iter(int(number), url, Authorization, etag=etag)

    def authorize(self, username, password, scopes=None, note='', note_url='',
                  client_id='', client_secret=''):
        """Obtain an authorization token.

        The retrieved token will allow future consumers to use the API without
        a username and password.

        :param str username: (required)
        :param str password: (required)
        :param list scopes: (optional), areas you want this token to apply to,
            i.e., 'gist', 'user'
        :param str note: (optional), note about the authorization
        :param str note_url: (optional), url for the application
        :param str client_id: (optional), 20 character OAuth client key for
            which to create a token
        :param str client_secret: (optional), 40 character OAuth client secret
            for which to create the token
        :returns: :class:`Authorization <Authorization>`
        """
        json = None

        if username and password:
            url = self._build_url('authorizations')
            data = {'note': note, 'note_url': note_url,
                    'client_id': client_id, 'client_secret': client_secret}
            if scopes:
                data['scopes'] = scopes

            with self.session.temporary_basic_auth(username, password):
                json = self._json(self._post(url, data=data), 201)

        return self._instance_or_null(Authorization, json)

    def check_authorization(self, access_token):
        """Check an authorization created by a registered application.

        OAuth applications can use this method to check token validity
        without hitting normal rate limits because of failed login attempts.
        If the token is valid, it will return True, otherwise it will return
        False.

        :returns: bool
        """
        p = self.session.params
        auth = (p.get('client_id'), p.get('client_secret'))
        if access_token and auth:
            url = self._build_url('applications', str(auth[0]), 'tokens',
                                  str(access_token))
            resp = self._get(url, auth=auth, params={
                'client_id': None, 'client_secret': None
            })
            return self._boolean(resp, 200, 404)
        return False

    def create_gist(self, description, files, public=True):
        """Create a new gist.

        If no login was provided, it will be anonymous.

        :param str description: (required), description of gist
        :param dict files: (required), file names with associated dictionaries
            for content, e.g. ``{'spam.txt': {'content': 'File contents
            ...'}}``
        :param bool public: (optional), make the gist public if True
        :returns: :class:`Gist <github3.gists.Gist>`
        """
        new_gist = {'description': description, 'public': public,
                    'files': files}
        url = self._build_url('gists')
        json = self._json(self._post(url, data=new_gist), 201)
        return self._instance_or_null(Gist, json)

    @requires_auth
    def create_issue(self, owner, repository, title, body=None, assignee=None,
                     milestone=None, labels=[]):
        """Create an issue on the project 'repository' owned by 'owner'
        with title 'title'.

        ``body``, ``assignee``, ``milestone``, ``labels`` are all optional.

        .. warning::

            This method retrieves the repository first and then uses it to
            create an issue. If you're making several issues, you should use
            :py:meth:`repository <github3.github.GitHub.repository>` and then
            use :py:meth:`create_issue
            <github3.repos.repo.Repository.create_issue>`

        :param str owner: (required), login of the owner
        :param str repository: (required), repository name
        :param str title: (required), Title of issue to be created
        :param str body: (optional), The text of the issue, markdown
            formatted
        :param str assignee: (optional), Login of person to assign
            the issue to
        :param int milestone: (optional), id number of the milestone to
            attribute this issue to (e.g. ``m`` is a :class:`Milestone
            <github3.issues.Milestone>` object, ``m.number`` is what you pass
            here.)
        :param list labels: (optional), List of label names.
        :returns: :class:`Issue <github3.issues.Issue>` if successful
        """
        repo = None
        if owner and repository and title:
            repo = self.repository(owner, repository)

        # repo can be None or a NullObject.
        # If repo is None, than one of owner, repository, or title were