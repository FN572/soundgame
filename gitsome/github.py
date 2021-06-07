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

import os
import platform
import sys
import urllib
import webbrowser

from .lib.github3 import null
from .lib.github3.exceptions import AuthenticationFailed, UnprocessableEntity
from .lib.img2txt import img2txt
import click
import feedparser
from requests.exceptions import MissingSchema, SSLError

from .config import Config
from .formatter import Formatter
from .rss_feed import language_rss_map
from .table import Table
from .view_entry import ViewEntry
from .web_viewer import WebViewer
from .utils import TextUtils


class GitHub(object):
    """Provide integration with the GitHub API.

    :type config: :class:`config.Config`
    :param config: An instance of `config.Config`.

    :type formatter: :class:`formatter.Formatter`
    :param formatter: An instance of `formatter.Formatter`.

    :type img2txt: callable
    :param img2txt: A callable fom img2txt.

    :type table: :class:`table.Table`
    :param table: An instance of `table.Table`.

    :type trend_parser: :class:`feedparser`
    :param trend_parser: An instance of `feedparser`.

    :type web_viewer: :class:`web_viewer.WebViewer`
    :param web_viewer: An instance of `web_viewer.WebViewer`.

    :type _base_url: str
    :param _base_url: The base GitHub or GitHub Enterprise url.
    """

    def __init__(self):
        self.config = Config()
        self.formatter = Formatter(self.config)
        self.img2txt = img2txt.img2txt
        self.table = Table(self.config)
        self.web_viewer = WebViewer(self.config)
        self.trend_parser = feedparser
        self.text_utils = TextUtils()
        self._base_url = 'https://github.com/'

    @property
    def base_url(self):
        return self.config.enterprise_url or self._base_url

    def add_base_url(self, url):
        """Add the base url if it is not already part of the given url.

        :type url: str
        :param url: The url.

        :return: The url including the base url.
        """
        return self.base_url + url if self.base_url not in url else url

    def authenticate(func):
        """Decorator that authenticates credentials.

        :type func: callable
        :param func: A method to execute if authorization passes.

        :return: The return value of `func` if authorization passes, or
            None if authorization fails.
        """
        def auth_wrapper(self, *args, **kwargs):
            self.config.authenticate()
            self.config.save_config()
            if self.config.check_auth():
                try:
                    return func(self, *args, **kwargs)
                except SSLError:
                    click.secho(('SSL cert verification failed.\n  Try running '
                                 'gh configure --enterprise\n  and type '
                                 "'n' when asked whether to verify SSL certs."),
                                fg=self.config.clr_error)
                except MissingSchema:
                    click.secho('Invalid GitHub Enterprise url',
                                fg=self.config.clr_error)
                except AuthenticationFailed:
                    self.config.print_auth_error()
        return auth_wrapper

    def avatar(self, url, text_avatar):
        """Display the user's avatar from the specified url.

        This method requires PIL.

        :type url: str
        :param url: The user's avatar image.

        :type text_avatar: bool
        :param text_avatar: Determines whether to view the profile avatar
            in plain text (True) or in ansi (False).
            On Windows this value is always set to True due to lack of
            support of `img2txt` on Windows.

        :rtype: str
        :return: The avatar.
        """
        if platform.system() == 'Windows':
            text_avatar = True
        avatar_enabled = self.config.enable_avatar
        avatar_text = ''
        if avatar_enabled:
            avatar = self.config.get_github_config_path(
                self.config.CONFIG_AVATAR)
            try:
                urllib.request.urlretrieve(url, avatar)
            except urllib.error.URLError:
                pass
            if os.path.exists(avatar):
                avatar_text = self.img2txt(avatar, ansi=(not text_avatar))
                avatar_text += '\n'
                os.remove(avatar)
        return avatar_text

    def avatar_setup(self, url, text_avatar):
        """Prepare to display the user's avatar from the specified url.

        This method requires PIL.

        :type url: str
        :param url: The user's avatar image.

        :type text_avatar: bool
        :param text_avatar: Determines whether to view the profile avatar
            in plain text (True) or in ansi (False).
            On Windows this value is always set to True due to lack of
            support of `img2txt` on Windows.

        :rtype: str
        :return: The avatar.
        """
        try:
            import PIL  # NOQA
            return self.avatar(url, text_avatar)
        except ImportError:
            avatar_text = click.style(('To view the avatar in your terminal, '
                                       'install the Python Image Library.\n'),
                                      fg=self.config.clr_message)
            return avatar_text

    def configure(self, enterprise):
        """Configure gitsome.

        Attempts to authenticate the user and to set up the user's news feed.

        If `gitsome` has not yet been configured, calling a `gh` command that
        requires authentication will automatically invoke the `configure`
        command.

        :type enterprise: bool
        :param enterprise: Determines whether to configure GitHub Enterprise.
        """
        self.config.authenticate(enterprise=enterprise, overwrite=True)
        self.config.prompt_news_feed()
        self.config.show_bash_completions_info()
        self.config.save_config()

    @authenticate
    def create_comment(self, user_repo_number, text):
        """Create a comment on the given issue.

        :type user_repo_number: str
        :param user_repo_number: The user/repo/issue_number.

        :type text: str
        :param text: The comment text.
        """
        try:
            user, repo, number = user_repo_number.split('/')
            int(number)  # Check for int
        except ValueError:
            click.secho(('Expected argument: user/repo/# and option -t '
                         '"comment".'),
                        fg=self.config.clr_error)
            return
        issue = self.config.api.issue(user, repo, number)
        issue_comment = issue.create_comment(text)
        if type(issue_comment) is not null.NullObject:
            click.secho('Created comment: ' + issue_comment.body,
                        fg=self.config.clr_message)
        else:
            click.secho('Error creating comment',
                        fg=self.config.clr_error)

    @authenticate
    def create_issue(self, user_repo, issue_title, issue_desc=''):
        """Create an issue.

        :type user_repo: str
        :param user_repo: The user/repo.

        :type issue_title: str
        :param issue_title: The issue title.

        :type issue_desc: str
        :param issue_desc: The issue body (optional).
        """
        try:
            user, repo_name = user_repo.split('/')
        except ValueError:
            click.secho('Expected argument: user/repo and option -t "title".',
                        fg=self.config.clr_error)
            return
        issue = self.config.api.create_issue(user,
                                             repo_name,
                                             issue_title,
                                             issue_desc)
        if type(issue) is not null.NullObject:
            body = self.text_utils.sanitize_if_none(issue.body)
            click.secho('Created issue: ' + issue.title + '\n' + body,
                        fg=self.config.clr_message)
        else:
            click.secho('Error creating issue.', fg=self.config.clr_error)

    @authenticate
    def create_repo(self, repo_name, repo_desc='', private=False):
        """Create a repo.

        :type repo_name: str
        :param repo_name: The repo name.

        :type repo_desc: str
        :param repo_desc: The repo description (optional).

        :type private: bool
        :param private: Determines whether the repo is private.  Default: False.
        """
        try:
            repo = self.config.api.create_repository(repo_name,
                                                     repo_desc,
                                                     private=private)
            desc = self.text_utils.sanitize_if_none(repo.description)
            click.secho(('Created repo: ' + repo.full_name + '\n' + desc),
                        fg=self.config.clr_message)
        except UnprocessableEntity as e:
            click.secho('Error creating repo: ' + str(e.msg),
                        fg=self.config.clr_error)

    @authenticate
    def emails(self):
        """List all the user's registered emails."""
        self.table.build_table_setup(self.config.api.emails(),
                                     self.formatter.format_email,
                                     limit=sys.maxsize,
                                     pager=False,
                                     build_urls=False)

    @authenticate
    def emojis(self, pager=False):
        """List all GitHub supported emojis.

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.
        """
        self.table.build_table_setup(self.config.api.emojis(),
                                     self.formatter.format_emoji,
                                     limit=sys.maxsize,
                                     pager=pager,
                                     build_urls=False)

    @authenticate
    def feed(self, user_or_repo='', private=False, pager=False):
        """List all activity for the given user or repo.

        If `user_or_repo` is not provided, uses the logged in user's news feed
        seen while visiting https://github.com.  If `user_or_repo` is provided,
        shows either the public or `[-p/--private]` feed activity of the user
        or repo.

        :type user_or_repo: str
        :param user_or_repo: The user or repo to list events for (optional).
            If no entry, defaults to the logged in user's feed.

        :type private: bool
        :param private: Determines whether to show the private events (True)
            or public events (False).

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.
        """
        click.secho('Listing events...', fg=self.config.clr_message)
        if user_or_repo == '':
            if self.config.user_feed is None:
                self.config.prompt_news_feed()
                self.config.save_config()
            if self.config.user_feed:
                items = self.trend_parser.parse(self.config.user_feed)
                self.table.build_table_setup_feed(
                    items,
                    self.formatter.format_feed_entry,
                    pager)
        else:
            if '/' in user_or_repo:
                user, repo = user_or_repo.split('/')
                repo = self.config.api.repository(user, repo)
                items = repo.events()
            else:
                public = False if private else True
                items = self.config.api.user(user_or_repo).events(public=public)
            self.table.build_table_setup(
                items,
                self.formatter.format_event,
                limit=sys.maxsize,
                pager=pager,
                build_urls=False)

    @authenticate
    def followers(self, user, pager=False):
        """List all followers and the total follower count.

        :type user: str
        :param user: The user login (optional).
            If None, returns the followers of the logged in user.

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.
        """
        if user is None:
            user = self.config.user_login
        self.table.build_table_setup_user(
            self.config.api.followers_of(user),
            self.formatter.format_user,
            limit=sys.maxsize,
            pager=pager)

    @authenticate
    def following(self, user, pager=False):
        """List all followed users and the total followed count.

        :type user: str
        :param user: The user login.
            If None, returns the followed users of the logged in user.

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.
        """
        if user is None:
            user = self.config.user_login
        self.table.build_table_setup_user(
            self.config.api.followed_by(user),
            self.formatter.format_user,
            limit=sys.maxsize,
            pager=pager)

    @authenticate
    def gitignore_template(self, language):
        """Output the gitignore template for the given language.

        :type language: str
        :param language: The language.
        """
        template = self.config.api.gitignore_template(language)
        if template:
            click.secho(template, fg=self.config.clr_message)
        else:
            click.secho(('Invalid case-sensitive template requested, run the '
                         'following command to see available templates:\n'
                         '    gh gitignore-templates'),
                        fg=self.config.clr_error)

    @authenticate
    def gitignore_templates(self, pager=False):
        """Output all supported gitignore templates.

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.
        """
        self.table.build_table_setup(
            self.config.api.gitignore_templates(),
            self.formatter.format_gitignore_template_name,
            limit=sys.maxsize,
            pager=pager,
            build_urls=False)
        click.secho(('  Run the following command to view or download a '
                     '.gitignore file:\n'
                     '    View:     gh gitignore Python\n'
                     '    Download: gh gitignore Python > .gitignore\n'),
                    fg=self.config.clr_message)

    @authenticate
    def issue(self, user_repo_number):
        """Output detailed information about the given issue.

        :type user_repo_number: str
        :param user_repo_number: The user/repo/issue_number.
        """
        try:
            user, repo, number = user_repo_number.split('/')
            int(number)  # Check for int
        except ValueError:
            click.secho('Expected argument: user/repo/#.',
                        fg=self.config.clr_error)
            return
        url = (self.base_url + user + '/' + repo + '/' +
               'issues/' + number)
        self.web_viewer.view_url(url)

    @authenticate
    def issues(self, issues_list, limit=1000, pager=False, sort=True):
        """List all issues.

        :type issues_list: list
        :param issues_list: A list of `github3` Issues.

        :type limit: int
        :param limit: The number of items to display.

        :type pager: bool
        :param pager: Determines whether to show the output in a pager,
            if available.

        :type sort: bool
        :param sort: De