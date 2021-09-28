# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from ..decorators import requires_auth
from ..exceptions import error_for
from ..models import GitHubCore
from .. import utils
from uritemplate import URITemplate


class Release(GitHubCore):

    """The :class:`Release <Release>