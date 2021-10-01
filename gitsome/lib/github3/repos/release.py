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
        self.prerelease = release.get('prerelease')
        #: Date the release was published
        self.published_at = self._strptime(release.get('published_at'))
        #: Name of the tag
        self.tag_name = release.get('tag_name')
        #: URL to download a tarball of the release
        self.tarball_url = release.get('tarball_url')
        #: "Commit" that this release targets
        self.target_commitish = release.get('target_commitish')
        upload_url = release.get('upload_url')
        #: URITemplate to upload an asset with
        self.upload_urlt = URITemplate(upload_url) if upload_url else None
        #: URL to download a zipball of the release
        self.zipball_url = release.get('zipball_url')

    def _repr(self):
        return '<Release [{0}]>'.format(self.name)

    def archive(self, format, path=''):
        """Get the tarball or zipball archive for this release.

        :param str format: (required), accepted values: ('tarball',
            'zipball')
        :param path: (optional), path where the file should be saved
            to, default is the filename provided in the headers and will be
            written in the current directory.
            it can take a file-like object as well
        :type path: str, file
        :returns: bool -- True if successful, False otherwise

        """
        resp = None
        if format in ('tarball', 'zipball'):
            repo_url = self._api[:self._api.rfind('/releases')]
            url = self._build_url(format, self.tag_name, base_url=repo_url)
            resp = self._get(url, allow_redirects=True, stream=True)

        if resp and self._boolean(resp, 200, 404):
            utils.stream_response_to_file(resp, path)
            return True
        return False

    def asset(self, asset_id):
        """Retrieve the asset from this release with ``asset_id``.

        :param int asset_id: ID of the Asset to retrieve
        :returns: :class:`~github3.repos.release.Asset`
        """
        json = None
        if int(asset_id) > 0:
            i = self._api.rfind('/')
            url = self._build_url('assets', str(asset_id),
                                  base_url=self._api[:i])
            json = self._json(self._get(url), 200)
        return self._instance_or_null(Asse