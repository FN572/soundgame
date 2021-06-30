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

import click

from .github import GitHub


click.disable_unicode_literals_warning = True
pass_github = click.make_pass_decorator(GitHub)


class GitHubCli(object):
    """The GitHubCli, builds `click` commands and runs `GitHub` methods."""

    @click.group()
    @click.pass_context
    def cli(ctx):
        """Main entry point for GitHubCli.

        :type ctx: :class:`click.core.Context`
        :param ctx: An instance of click.core.Context that stores an instance
            of `github.GitHub`.
        """
        # Create a GitHub object and remember it as the context object.
        # From this point onwards other commands can refer to it by using the
        # @pass_github decorator.
        ctx.obj = GitHub()

    @cli.command()
    @click.option('-e', '--enterprise', is_flag=True)
    @pass_github
    def configure(github, enterprise):
        """Configure gitsome.

        Attempts to authenticate the user and to set up the user's news feed.

        Usage/Example(s):
            gh configure
            gh configure -e
            gh configure --enterprise

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.GitHub`.
        :type enterprise: bool
        :param enterprise: Determines whether to configure GitHub Enterprise.
            Default: False.
        """
        github.configure(enterprise)

    @cli.command('create-comment')
    @click.argument('user_repo_number')
    @click.option('-t', '--text')
    @pass_github
    def create_comment(github, user_repo_number, text):
        """Create a comment on the given issue.

        Usage:
            gh create-comment [user_repo_number] [-t/--text]

        Example(s):
            gh create-comment donnemartin/saws/1 -t "hello world"
            gh create-comment donnemartin/saws/1 --text "hello world"

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.GitHub`.

        :type user_repo_number: str
        :param user_repo_number: The user/repo/issue_number.

        :type text: str
        :param text: The comment text.
        """
        github.create_comment(user_repo_number, text)

    @cli.command('create-issue')
    @click.argument('user_repo')
    @click.option('-t', '--issue_title')
    @click.option('-d', '--issue_desc', required=False)
    @pass_github
    def create_issue(github, user_repo, issue_title, issue_desc):
        """Create an issue.

        Usage:
            gh create-issue [user_repo] [-t/--issue_title] [-d/--issue_desc]

        Example(s):
            gh create-issue donnemartin/gitsome -t "title"
            gh create-issue donnemartin/gitsome -t "title" -d "desc"
            gh create-issue donnemartin/gitsome --issue_title "title" --issue_desc "desc"  # NOQA

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.GitHub`.

        :type user_repo: str
        :param user_repo: The user/repo.

        :type issue_title: str
        :param issue_title: The issue title.

        :type issue_desc: str
        :param issue_desc: The issue body (optional).
        """
        github.create_issue(user_repo, issue_title, issue_desc)

    @cli.command('create-repo')
    @click.argument('repo_name')
    @click.option('-d', '--repo_desc', required=False)
    @click.option('-pr', '--private', is_flag=True)
    @pass_github
    def create_repo(github, repo_name, repo_desc, private):
        """Create a repo.

        Usage:
            gh create-repo [repo_name] [-d/--repo_desc] [-pr/--private]

        Example(s):
            gh create-repo repo_name
            gh create-repo repo_name -d "desc"
            gh create-repo repo_name --repo_desc "desc"
            gh create-repo repo_name -pr
            gh create-repo repo_name --repo_desc "desc" --private

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.GitHub`.

        :type repo_name: str
        :param repo_name: The repo name.

        :type repo_desc: str
        :param repo_desc: The repo description (optional).

        :type private: bool
        :param private: Determines whether the repo is private.  Default: False.
        """
        github.create_repo(repo_name, repo_desc, private)

    @cli.command()
    @pass_github
    def emails(github):
        """List all the user's registered emails.

        Usage/Example(s):
            gh emails

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.GitHub`.
        """
        github.emails()

    @cli.command()
    @click.option('-p', '--pager', is_flag=True)
    @pass_github
    def emojis(github, pager):
        """List all GitHub supported emojis.

        Usage:
            gh emojis [-p/--pager]

        Example(s):
            gh emojis | grep octo

        :type github: :class:`github.GitHub`
        :param github: An instance of `github.