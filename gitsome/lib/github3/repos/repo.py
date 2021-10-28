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
        ie_url_t = repo.get('issue_events_url')
        #: Issue events URL Template. Expand with ``number``
        self.issue_events_urlt = URITemplate(ie_url_t) if ie_url_t else None

        assignees = repo.get('assignees_url')
        #: Assignees URL Template. Expand with ``user``
        self.assignees_urlt = URITemplate(assignees) if assignees else None

        branches = repo.get('branches_url')
        #: Branches URL Template. Expand with ``branch``
        self.branches_urlt = URITemplate(branches) if branches else None

        blobs = repo.get('blobs_url')
        #: Blobs URL Template. Expand with ``sha``
        self.blobs_urlt = URITemplate(blobs) if blobs else None

        git_tags = repo.get('git_tags_url')
        #: Git tags URL Template. Expand with ``sha``
        self.git_tags_urlt = URITemplate(git_tags) if git_tags else None

        git_refs = repo.get('git_refs_url')
        #: Git refs URL Template. Expand with ``sha``
        self.git_refs_urlt = URITemplate(git_refs) if git_refs else None

        trees = repo.get('trees_url')
        #: Trres URL Template. Expand with ``sha``
        self.trees_urlt = URITemplate(trees) if trees else None

        statuses = repo.get('statuses_url')
        #: Statuses URL Template. Expand with ``sha``
        self.statuses_urlt = URITemplate(statuses) if statuses else None

        commits = repo.get('commits_url')
        #: Commits URL Template. Expand with ``sha``
        self.commits_urlt = URITemplate(commits) if commits else None

        commits = repo.get('git_commits_url')
        #: Git commits URL Template. Expand with ``sha``
        self.git_commits_urlt = URITemplate(commits) if commits else None

        comments = repo.get('comments_url')
        #: Comments URL Template. Expand with ``number``
        self.comments_urlt = URITemplate(comments) if comments else None

        comments = repo.get('review_comments_url')
        #: Pull Request Review Comments URL
        self.review_comments_url = URITemplate(comments) if comments else None

        comments = repo.get('review_comment_url')
        #: Pull Request Review Comments URL Template. Expand with ``number``
        self.review_comment_urlt = URITemplate(comments) if comments else None

        comments = repo.get('issue_comment_url')
        #: Issue comment URL Template. Expand with ``number``
        self.issue_comment_urlt = URITemplate(comments) if comments else None

        contents = repo.get('contents_url')
        #: Contents URL Template. Expand with ``path``
        self.contents_urlt = URITemplate(contents) if contents else None

        compare = repo.get('compare_url')
        #: Comparison URL Template. Expand with ``base`` and ``head``
        self.compare_urlt = URITemplate(compare) if compare else None

        archive = repo.get('archive_url')
        #: Archive URL Template. Expand with ``archive_format`` and ``ref``
        self.archive_urlt = URITemplate(archive) if archive else None

        issues = repo.get('issues_url')
        #: Issues URL Template. Expand with ``number``
        self.issues_urlt = URITemplate(issues) if issues else None

        pulls = repo.get('pulls_url')
        #: Pull Requests URL Template. Expand with ``number``
        self.pulls_urlt = URITemplate(pulls) if issues else None

        miles = repo.get('milestones_url')
        #: Milestones URL Template. Expand with ``number``
        self.milestones_urlt = URITemplate(miles) if miles else None

        notif = repo.get('notifications_url')
        #: Notifications URL Template. Expand with ``since``, ``all``,
        #: ``participating``
        self.notifications_urlt = URITemplate(notif) if notif else None

        labels = repo.get('labels_url')
        #: Labels URL Template. Expand with ``name``
        self.labels_urlt = URITemplate(labels) if labels else None

    def _repr(self):
        return '<Repository [{0}]>'.format(self)

    def __str__(self):
        return self.full_name

    def _create_pull(self, data):
        self._remove_none(data)
        json = None
        if data:
            url = self._build_url('pulls', base_url=self._api)
            json = self._json(self._post(url, data=data), 201)
        return self._instance_or_null(PullRequest, json)

    @requires_auth
    def add_collaborator(self, username):
        """Add ``username`` as a collaborator to a repository.

        :param username: (required), username of the user
        :type username: str or :class:`User <github3.users.User>`
        :returns: bool -- True if successful, False otherwise
        """
        if not username:
            return False
        url = self._build_url('collaborators', str(username),
                              base_url=self._api)
        return self._boolean(self._put(url), 204, 404)

    def archive(self, format, path='', ref='master'):
        """Get the tarball or zipball archive for this repo at ref.

        See: http://developer.github.com/v3/repos/contents/#get-archive-link

        :param str format: (required), accepted values: ('tarball',
            'zipball')
        :param path: (optional), path where the file should be saved
            to, default is the filename provided in the headers and will be
            written in the current directory.
            it can take a file-like object as well
        :type path: str, file
        :param str ref: (optional)
        :returns: bool -- True if successful, False otherwise

        """
        resp = None
        if format in ('tarball', 'zipball'):
            url = self._build_url(format, ref, base_url=self._api)
            resp = self._get(url, allow_redirects=True, stream=True)

        if resp and self._boolean(resp, 200, 404):
            stream_response_to_file(resp, path)
            return True
        return False

    def asset(self, id):
        """Return a single asset.

        :param int id: (required), id of the asset
        :returns: :class:`Asset <github3.repos.release.Asset>`
        """
        data = None
        if int(id) > 0:
            url = self._build_url('releases', 'assets', str(id),
                                  base_url=self._api)
            data = self._json(self._get(url, headers=Release.CUSTOM_HEADERS),
                              200)
        return self._instance_or_null(Asset, data)

    def assignees(self, number=-1, etag=None):
        r"""Iterate over all assignees to which an issue may be assigned.

        :param int number: (optional), number of assignees to return. Default:
            -1 returns all available assignees
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of :class:`User <github3.users.User>`\ s
        """
        url = self._build_url('assignees', base_url=self._api)
        return self._iter(int(number), url, User, etag=etag)

    def blob(self, sha):
        """Get the blob indicated by ``sha``.

        :param str sha: (required), sha of the blob
        :returns: :class:`Blob <github3.git.Blob>` if successful, otherwise
            None
        """
        url = self._build_url('git', 'blobs', sha, base_url=self._api)
        json = self._json(self._get(url), 200)
        return self._instance_or_null(Blob, json)

    def branch(self, name):
        """Get the branch ``name`` of this repository.

        :param str name: (required), branch name
        :type name: str
        :returns: :class:`Branch <github3.repos.branch.Branch>`
        """
        json = None
        if name:
            url = self._build_url('branches', name, base_url=self._api)
            json = self._json(self._get(url, headers=Branch.PREVIEW_HEADERS),
                              200)
        return self._instance_or_null(Branch, json)

    def branches(self, number=-1, protected=False, etag=None):
        r"""Iterate over the branches in this repository.

        :param int number: (optional), number of branches to return. Default:
            -1 returns all branches
        :param bool protected: (optional), True lists only protected branches.
            Default: False
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of
            :class:`Branch <github3.repos.branch.Branch>`\ es
        """
        url = self._build_url('branches', base_url=self._api)
        params = {'protected': '1'} if protected else None
        return self._iter(int(number), url, Branch, params, etag=etag,
                          headers=Branch.PREVIEW_HEADERS)

    def code_frequency(self, number=-1, etag=None):
        """Iterate over the code frequency per week.

        Returns a weekly aggregate of the number of additions and deletions
        pushed to this repository.

        :param int number: (optional), number of weeks to return. Default: -1
            returns all weeks
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of lists ``[seconds_from_epoch, additions,
            deletions]``

        .. note:: All statistics methods may return a 202. On those occasions,
                  you will not receive any objects. You should store your
                  iterator and check the new ``last_status`` attribute. If it
                  is a 202 you should wait before re-requesting.

        .. versionadded:: 0.7

        """
        url = self._build_url('stats', 'code_frequency', base_url=self._api)
        return self._iter(int(number), url, list, etag=etag)

    def collaborators(self, number=-1, etag=None):
        r"""Iterate over the collaborators of this repository.

        :param int number: (optional), number of collaborators to return.
            Default: -1 returns all comments
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of :class:`User <github3.users.User>`\ s
        """
        url = self._build_url('collaborators', base_url=self._api)
        return self._iter(int(number), url, User, etag=etag)

    def comments(self, number=-1, etag=None):
        r"""Iterate over comments on all commits in the repository.

        :param int number: (optional), number of comments to return. Default:
            -1 returns all comments
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of
            :class:`RepoComment <github3.repos.comment.RepoComment>`\ s
        """
        url = self._build_url('comments', base_url=self._api)
        return self._iter(int(number), url, RepoComment, etag=etag)

    def commit(self, sha):
        """Get a single (repo) commit.

        See :func:`git_commit` for the Git Data Commit.

        :param str sha: (required), sha of the commit
        :returns: :class:`RepoCommit <github3.repos.commit.RepoCommit>` if
            successful, otherwise None
        """
        url = self._build_url('commits', sha, base_url=self._api)
        json = self._json(self._get(url), 200)
        return self._instance_or_null(RepoCommit, json)

    def commit_activity(self, number=-1, etag=None):
        """Iterate over last year of commit activity by week.

        See: http://developer.github.com/v3/repos/statistics/

        .. note:: All statistics methods may return a 202. On those occasions,
                  you will not receive any objects. You should store your
                  iterator and check the new ``last_status`` attribute. If it
                  is a 202 you should wait before re-requesting.

        .. versionadded:: 0.7

        :param int number: (optional), number of weeks to return. Default -1
            will return all of the weeks.
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of dictionaries
        """
        url = self._build_url('stats', 'commit_activity', base_url=self._api)
        return self._iter(int(number), url, dict, etag=etag)

    def commit_comment(self, comment_id):
        """Get a single commit comment.

        :param int comment_id: (required), id of the comment used by GitHub
        :returns: :class:`RepoComment <github3.repos.comment.RepoComment>` if
            successful, otherwise None
        """
        url = self._build_url('comments', str(comment_id), base_url=self._api)
        json = self._json(self._get(url), 200)
        return self._instance_or_null(RepoComment, json)

    def commits(self, sha=None, path=None, author=None, number=-1, etag=None,
                since=None, until=None):
        r"""Iterate over commits in this repository.

        :param str sha: (optional), sha or branch to start listing commits
            from
        :param str path: (optional), commits containing this path will be
            listed
        :param str author: (optional), GitHub login, real name, or email to
            filter commits by (using commit author)
        :param int number: (optional), number of comments to return. Default:
            -1 returns all comments
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :param since: (optional), Only commits after this date will
            be returned. This can be a ``datetime`` or an ``ISO8601`` formatted
            date string.
        :type since: datetime or string
        :param until: (optional), Only commits before this date will
            be returned. This can be a ``datetime`` or an ``ISO8601`` formatted
            date string.
        :type until: datetime or string

        :returns: generator of
            :class:`RepoCommit <github3.repos.commit.RepoCommit>`\ s
        """
        params = {'sha': sha, 'path': path, 'author': author,
                  'since': timestamp_parameter(since),
                  'until': timestamp_parameter(until)}

        self._remove_none(params)
        url = self._build_url('commits', base_url=self._api)
        return self._iter(int(number), url, RepoCommit, params, etag)

    def compare_commits(self, base, head):
        """Compare two commits.

        :param str base: (required), base for the comparison
        :param str head: (required), compare this against base
        :returns: :class:`Comparison <github3.repos.comparison.Comparison>` if
            successful, else None
        """
        url = self._build_url('compare', base + '...' + head,
                              base_url=self._api)
        json = self._json(self._get(url), 200)
        return self._instance_or_null(Comparison, json)

    def contributor_statistics(self, number=-1, etag=None):
        """Iterate over the contributors list.

        See also: http://developer.github.com/v3/repos/statistics/

        .. note:: All statistics methods may return a 202. On those occasions,
                  you will not receive any objects. You should store your
                  iterator and check the new ``last_status`` attribute. If it
                  is a 202 you should wait before re-requesting.

        .. versionadded:: 0.7

        :param int number: (optional), number of weeks to return. Default -1
            will return all of the weeks.
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of
            :class:`ContributorStats <github3.repos.stats.ContributorStats>`
        """
        url = self._build_url('stats', 'contributors', base_url=self._api)
        return self._iter(int(number), url, ContributorStats, etag=etag)

    def contributors(self, anon=False, number=-1, etag=None):
        r"""Iterate over the contributors to this repository.

        :param bool anon: (optional), True lists anonymous contributors as
            well
        :param int number: (optional), number of contributors to return.
            Default: -1 returns all contributors
        :param str etag: (optional), ETag from a previous request to the same
            endpoint
        :returns: generator of :class:`User <github3.users.User>`\ s
        """
        url = self._build_url('contributors', base_url=self._api)
        params = {}
        if anon:
            params = {'anon': 'true'}
        return self._iter(int(number), url, User, params, etag)

    @requires_auth
    def create_blob(self, content, encoding):
        """Create a blob with ``content``.

        :param str content: (required), content of the blob
        :param str encoding: (required), ('base64', 'utf-8')
        :returns: string of the SHA returned
        """
        sha = ''
        if encoding in ('base64', 'utf-8'):
            url = self._build_url('git', 'blobs', base_url=self._api)
            data = {'content': content, 'encoding': encoding}
            json = self._json(self._post(url, data=data), 201)
            if json:
                sha = json.get('sha')
        return sha

    @requires_auth
    def create_comment(self, body, sha, path=None, position=None, line=1):
        """Create a comment on a commit.

        :param str body: (required), body of the message
        :param str sha: (required), commit id
        :param str path: (optional), relative path of the file to comment
            on
        :param str position: (optional), line index in the diff to comment on
        :param int line: (optional), line number of the file to comment on,
            default: 1
        :returns: :class:`RepoComment <github3.repos.comment.RepoComment>` if
            successful, otherwise None

        """
        json = None
        if body and sha and (line and int(line) > 0):
            data = {'body': body, 'line': line, 'path': path,
                    'position': position}
            self._remove_none(data)
            url = self._build_url('commits', sha, 'comments',
                                  base_url=self._api)
            json = self._json(self._post(url, data=data), 201)
        return self._instance_or_null(RepoComment, json)

    @requires_auth
    def create_commit(self, message, tree, parents, author=None,
                      committer=None):
        """Create a commit on this repository.

        :param str message: (required), commit message
        :param str tree: (required), SHA of the tree object this
            commit points to
        :param list parents: (required), SHAs of the commits that were parents
            of this commit. If empty, the commit will be written as the root
            commit.  Even if there is only one parent, this should be an
            array.
        :param dict author: (optional), if omitted, GitHub will
            use the authenticated user's credentials and the current
            time. Format: {'name': 'Committer Name', 'email':
            'name@example.com', 'date': 'YYYY-MM-DDTHH:MM:SS+HH:00'}
        :param dict committer: (optional), if ommitted, GitHub will use the
            author parameters. Should be the same format as the author
            parameter.
        :returns: :class:`Commit <github3.git.Commit>` if successful, else
            None
        """
        json = None
        if message and tree and isinstance(parents, list):
            url = self._build_url('git', 'commits', base_url=self._api)
            data = {'message': message, 'tree': tree, 'parents': parents,
                    'author': author, 'committer': committer}
            self._remove_none(data)
            json = self._json(self._post(url, data=data), 201)
        return self._instance_or_null(Commit, json)

    @requires_auth
    def create_deployment(self, ref, force=False, payload='',
                          auto_merge=False, description='', environment=None):
        """Create a deployment.

        :param str ref: (required), The ref to deploy. This can be a branch,
            tag, or sha.
        :param bool force: Optional parameter to bypass any ahead/behind
            checks or commit status checks. Default: False
        :param str payload: Optional JSON payload with extra information about
            the deployment. Default: ""
        :param bool auto_merge: Optional parameter to merge the default branch
            into the requested deployment branch if necessary. Default: False
        :param str description: Optional short description. Default: ""
        :param str environment: Optional name for the target deployment
            environment (e.g., production, staging, qa). Default: "production"
        :returns: :class:`Deployment <github3.repos.deployment.Deployment>`
        """
        json = None
        if ref:
            url = self._build_url('deployments', base_url=self._api)
            data = {'ref': ref, 'force': force, 'payload': payload,
                    'auto_merge': auto_merge, 'description': description,
                    'environment': environment}
            self._remove_none(data)
            json = self._json(self._post(url, data=data),
                              201)
        return self._instance_or_null(Deployment, json)

    @requires_auth
    def create_file(self, path, message, content, branch=None,
                    committer=None, author=None):
        """Create a file in this repository.

        See also: http://developer.github.com/v3/repos/contents/#create-a-file

        :param str path: (required), path of the file in the repository
        :param str message: (required), commit message
        :param bytes content: (required), the actual data in the file
        :param str branch: (optional), branch to create the commit on.
            Defaults to the default branch of the repository
        :param dict committer: (optional), if no information is given the
            authenticated user's information will be used. You must specify
            both a name and email.
        :param dict author: (optional), if omitted this will be filled in with
            committer information. If passed, you must specify both a name and
            email.
        :returns: {
            'content': :class:`Contents <github3.repos.contents.Contents>`:,
            'commit': :class:`Commit <github3.git.Commit>`}

        """
        if content and not isinstance(content, byt