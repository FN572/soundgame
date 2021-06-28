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

  