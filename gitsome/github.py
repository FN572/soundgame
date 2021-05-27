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
     