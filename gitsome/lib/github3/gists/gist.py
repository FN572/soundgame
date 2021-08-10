# -*- coding: utf-8 -*-
"""
github3.gists.gist
==================

This module contains the Gist class alone for simplicity.

"""
from __future__ import unicode_literals

from json import dumps
from ..models import GitHubCore
from ..decorators import requires_auth
from .comment import GistComment
from .file import GistFile
from .history import GistHistory
from ..users import User


class Gist(GitHubCore):

    """This object holds all the information returned by Github about a gist.

    With it you can comment on or fork the gist (assuming you are
    authenticated), edit or delete the gist (assuming you own it).  You can
    also "star" or "unstar" the gist (again assuming you have authenticated).

    Two gist instances can be checked like so::

        g1 == g2
        g1 != g2

    And is equivalent to::

        g1.id == g2.id
        g1.id != g2.id

    See also: http://developer.github.com/v3/gists/

    """

    def _update_attributes(self, data):
        #: Number of comments on this gist
        self.comments_count = data.get('comments', 0)

        #: Unique id for this gist.
        self.id = '{0}'.format(data.get('id', ''))

        #: Description of the gist