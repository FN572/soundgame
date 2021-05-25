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

    :type config: :class: