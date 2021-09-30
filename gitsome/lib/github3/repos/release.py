# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from ..decorators import requires_auth
from ..exceptions import error_for
from ..models import GitHubCore
from .. import utils
from uritemplate import URITemplate


class Release(GitHubCore):

    """The :class:`Release <Release>` object.

    It holds the information GitHub returns about a release from a
    :class:`Repository <github3.repos.repo.Repository>`.

    """

    CUSTOM_HEADERS = {'Accept': 'application/vnd.github.manifold-preview'}

    def _update_attributes(self, release):
        self._api = release.get('url')
        #: List of :class:`Asset <Asset>` objects for this release
        self.original_assets = [
            Asset(i, self) for i in release.get('assets', [])
        ]
        #: URL for uploaded assets
        self.assets_url = release.get('assets_url')
        #: Body of the release (the description)
        self.body = release.get('body')
        #: Date the release was created
        self.created_at = self._strptime(release.get('created_at'))
        #: Boolean whether value is True or False
        self.draft = release.get('draft')
        #: HTML URL of the release
        self.html_url = release.get('html_url')
        #: GitHub id
        self.id = release.get('id')
        #: Name given to the release
        self.name = release.get('name')
        #: Boolean whether release is a prerelease
        s