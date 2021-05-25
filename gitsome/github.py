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
        """Ad