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

import mock
from compat import unittest

from click.testing import CliRunner

from gitsome.githubcli import GitHubCli


class GitHubCliTest(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.github_cli = GitHubCli()
        self.limit = 1000

    def test_cli(self):
        result = self.runner.invoke(self.github_cli.cli)
        assert result.exit_code == 0

    @mock.patch('gitsome.githubcli.GitHub.configure')
    def test_configure(self, mock_gh_call):
        result = self.runner.invoke(self.github_cli.cli, ['configure'])
        mock_gh_call.assert_called_with(False)
        assert result.exit_code == 0

    @mock.patch('gitsome.githubcli.GitHub.create_comment')
    def test_create_comment(self, mock_gh_call):
        result = self.runner.invoke(self.github_cli.cli,
                      